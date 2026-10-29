# AI in Java

Most Java teams do not train models. They load a trained model for inference, or call a hosted LLM over HTTP, and wrap the call in ordinary service code. Interviewers ask where the boundary lies, which libraries fit, and how you make an AI call reliable, observable, and secure in production.

## Core concepts

### Training versus inference

- **Training** fits model weights to data. It is compute-heavy and iterative, and the Python ecosystem (PyTorch, TensorFlow, scikit-learn) dominates it.
- **Inference** runs a trained model on new inputs. It is latency-sensitive and is what a Java service usually does.

A common split: data scientists train in Python, export the model in a portable format, and a Java service loads it and exposes predictions through an API. Java can also train with DeepLearning4J, but that is less common outside JVM-only shops.

### Options for Java

| Option | What it does | Fits when |
|--------|--------------|-----------|
| ONNX Runtime (Java API) | Runs ONNX models from many frameworks | You want framework-neutral inference |
| TensorFlow Java | Loads TensorFlow SavedModels for inference | The model already ships as a SavedModel |
| DeepLearning4J | Builds and trains networks on the JVM | Pure-Java training and inference |
| Hosted LLM APIs over HTTP | Calls a provider's model | You need a general language model |
| Spring AI | Spring abstractions over chat, embeddings, tools, and vector stores | Spring Boot services that call LLMs or build RAG |
| Model server (TensorFlow Serving, Triton, TorchServe) | Serves models as separate services | Several models, batching, GPUs, independent scaling |

Check current versions and artifact coordinates in each project's documentation before adding dependencies. Library APIs change between major releases.

### TensorFlow Java

TensorFlow's Java binding loads a SavedModel and runs its serving signature. The model is closed when you finish, so use try-with-resources:

```java
import org.tensorflow.SavedModelBundle;
import org.tensorflow.Session;

public final class ModelLoader {
    public static void main(String[] args) {
        try (SavedModelBundle model = SavedModelBundle.load("models/churn/1", "serve")) {
            Session session = model.session();
            // Build input tensors, then call session.runner().feed(...).fetch(...).run()
            System.out.println("Model loaded, session open: " + (session != null));
        }
    }
}
```

Points to remember: tensor creation and closing need care, because native memory sits outside the garbage collector. Inference runs on CPU unless you add a GPU build of the native library. Training is primarily done elsewhere.

### DeepLearning4J

DL4J builds networks with a configuration builder, trains them on `DataSetIterator` inputs, and runs `output()` for predictions. Its ND4J backend supports CPU and CUDA GPUs. Pick it when the whole pipeline should stay on the JVM. Its ecosystem of pretrained models is smaller than the Python one.

### Calling a hosted LLM over HTTP

The JDK's built-in `java.net.http` client is enough for a plain call. The request is JSON with a model identifier, a token limit, and messages. The API key comes from the environment or a secret store, never from source code.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class HostedModelCall {
    public static void main(String[] args) throws Exception {
        String apiKey = System.getenv("ANTHROPIC_API_KEY");
        String model = System.getenv().getOrDefault("LLM_MODEL", "set-a-model-id");

        String body = """
                {
                  "model": "%s",
                  "max_tokens": 256,
                  "messages": [
                    {"role": "user", "content": "Explain dependency injection in two sentences."}
                  ]
                }
                """.formatted(model);

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://api.anthropic.com/v1/messages"))
                .header("x-api-key", apiKey)
                .header("anthropic-version", "2023-06-01")
                .header("content-type", "application/json")
                .timeout(java.time.Duration.ofSeconds(30))
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println(response.body()); // parse the JSON with Jackson or a similar library
    }
}
```

Use a real JSON library for building and reading payloads. String templates are fine for a demo, but escaping user input by hand is error-prone. Set a timeout on every outbound call, because a slow model call can otherwise hold a request thread indefinitely.

### Spring AI

Spring AI gives a portable API over chat models, embedding models, tool calling, and vector stores. Spring Boot auto-configures a `ChatClient.Builder` when a provider starter is on the classpath. The fluent API keeps the prompt, the user message, and the call in one chain:

```java
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

@Service
public class SupportAnswerService {

    private final ChatClient chatClient;

    public SupportAnswerService(ChatClient.Builder builder) {
        this.chatClient = builder.build();
    }

    public String answer(String question) {
        return chatClient.prompt()
                .system("You are a concise support assistant.")
                .user(question)
                .call()
                .content();
    }
}
```

Embeddings use the same pattern through an `EmbeddingModel`, and a `VectorStore` implementation handles storage and similarity search. Spring AI's API has changed across 0.x and 1.x releases, so match the documentation to your version.

### Tool calling

Tool calling lets the model request a Java method, which your code runs and whose result goes back to the model. Annotate a method with a clear description and keep its inputs narrow:

```java
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.stereotype.Component;

@Component
public class OrderTools {

    @Tool(description = "Returns the status of an order by its order ID")
    public String orderStatus(String orderId) {
        // Look up the order through the existing service layer, not raw SQL
        return "SHIPPED";
    }
}
```

Validate every argument the model supplies, and check authorisation inside the method. The model can request any tool you expose, so treat its arguments as untrusted input.

### Retries and failures

Provider calls fail with rate limits, timeouts, and transient server errors. Retry only errors that are safe to retry, with exponential backoff and a maximum attempt count. With Spring Retry:

```java
import java.io.IOException;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;

@Service
public class RetryingAnswerService {

    // Requires @EnableRetry on a configuration class
    @Retryable(retryFor = IOException.class, maxAttempts = 3,
            backoff = @Backoff(delay = 1000, multiplier = 2))
    public String ask(String prompt) throws IOException {
        // call the model client here; throw IOException for transient network failures
        return "stub answer for: " + prompt;
    }
}
```

Replace `IOException` with the transient exception type your client throws. Do not retry non-idempotent actions, such as a tool call that charges a card, without a safeguard. For cascading-failure protection, wrap the call in a circuit breaker such as Resilience4j, so that repeated provider failures fail fast instead of queuing requests.

### Observability

Track the operations that matter for AI calls: latency per model and operation, error rates by type, retries, and token usage. Micrometer records these with the same tooling as other Spring metrics:

```java
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;

@Service
public class TimedAnswerService {

    private final ChatClient chatClient;
    private final MeterRegistry registry;

    public TimedAnswerService(ChatClient.Builder builder, MeterRegistry registry) {
        this.chatClient = builder.build();
        this.registry = registry;
    }

    public String answer(String question) {
        Timer.Sample sample = Timer.start(registry);
        try {
            return chatClient.prompt().user(question).call().content();
        } finally {
            sample.stop(registry.timer("llm.request.duration", "operation", "answer"));
        }
    }
}
```

Log prompts and responses with care. They can contain personal data, so redact or sample them, and check your data-handling policy first.

## How it works / Step by step

A typical AI-backed endpoint:

1. Validate and authorise the request before any model call.
2. Retrieve context if the feature uses RAG, filtered by the user's permissions.
3. Build the prompt from fixed instructions, retrieved passages, and the user's question.
4. Call the model with a timeout, a token limit, and a retry policy.
5. Validate the output: parse structured responses, check citations, and apply business rules.
6. Record metrics and return the result.

## Production considerations

- **Latency**: model calls dominate. Stream responses when the UI can show partial text, cache repeated answers where it is safe, and batch offline work.
- **Cost**: cost follows token counts. Keep prompts lean, cap output length, and send simple tasks to smaller models.
- **Model artefacts**: version them with the service, record which model produced which output, and keep rollback paths.
- **Security**: keep keys in a secret manager. Protect against prompt injection and never give the model tools that act beyond the user's rights.
- **Deployment**: package the service as a container on a current LTS Java runtime. A base image such as an Eclipse Temurin 21 JRE is a common choice. Large model files belong in a volume or object store rather than the image, unless the image size is acceptable.
- **Scaling**: scale stateless API instances horizontally. Scale GPU-backed inference separately, and batch requests when throughput matters more than per-request latency.

## Common pitfalls

- Hard-coding keys, or logging full prompts that contain customer data.
- No timeout on the HTTP client, so threads pile up during a provider slowdown.
- Retrying every exception, including validation errors and non-idempotent actions.
- Trusting model output as valid JSON or as safe to execute.
- Mixing up training and inference in the design, and expecting Java to retrain a model in production.
- Pinning to an old SDK or model identifier without a migration plan.

!!! tip "Interview tip"
    **How would you integrate an LLM into an existing Spring Boot service?** Put the model behind a service class, not in the controller. Set timeouts and bounded retries, keep keys in configuration, and validate both input and output. Add metrics and a fallback, such as a cached answer or a plain error message, so the rest of the service keeps working when the provider is slow or unavailable.

## Quick recap

- Java usually handles inference and integration, while training is mostly done in Python.
- Choose a runtime by fit: ONNX Runtime or TensorFlow for exported models, DL4J for JVM-only pipelines, HTTP or Spring AI for hosted LLMs.
- Wrap model calls with timeouts, bounded retries, and circuit breakers.
- Validate arguments for tool calls and treat model output as untrusted.
- Measure latency, errors, and token use from day one.

**See also:** [LLMs and Transformers](llms-and-transformers.md), [RAG and Generative AI](rag-and-generative-ai.md), [AI integration section](../22-ai-integration/index.md), [ML Fundamentals](ml-fundamentals.md)
