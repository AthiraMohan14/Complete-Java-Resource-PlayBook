# AI & Java Integration

Integrating machine learning and AI in Java: model inference, frameworks, LLM APIs, and production deployment.

---

## ML in Java: Inference vs Training

### Training
Building models from data (typically Python/PyTorch/TensorFlow).

```
Python (ML expert)
├─ Collect data (10M+ samples)
├─ Feature engineering
├─ Train model (hours/days on GPU)
├─ Validate, tune hyperparameters
├─ Export model (PyTorch .pt, TensorFlow .pb)
└─ Save: model.pb, weights.h5
```

### Inference
Using trained models to make predictions (Java/Go/C++).

```
Java (production)
├─ Load pre-trained model
├─ Preprocess input
├─ Run prediction (milliseconds)
├─ Postprocess output
└─ Return result to API
```

**Workflow:**
```
Data Scientist (Python)
  Train model
    ↓
  Export: model.pb
    ↓
  Java Developer
    Load: model.pb
    Serve: REST API
    Deploy: Production
```

---

## TensorFlow Java

Google's TensorFlow with Java binding; run pre-trained models.

### Installation & Setup

```xml
<!-- Maven dependency -->
<dependency>
  <groupId>org.tensorflow</groupId>
  <artifactId>tensorflow</artifactId>
  <version>1.15.0</version>
</dependency>
```

### Loading & Running Model

```java
import org.tensorflow.SavedModelBundle;
import org.tensorflow.Session;
import org.tensorflow.Tensor;

public class MLInference {
    
    // Load pre-trained model
    SavedModelBundle model = SavedModelBundle.load(
        "path/to/model", 
        "serve"  // Tag (usually "serve" for inference)
    );
    
    Session session = model.session();
    
    // Prepare input
    float[][] input = {{1.0f, 2.0f, 3.0f}};
    Tensor inputTensor = Tensor.create(input);
    
    // Run inference
    Tensor outputTensor = session.runner()
        .feed("input_tensor", inputTensor)  // Input name
        .fetch("output_tensor")              // Output name
        .run()
        .get(0);
    
    // Extract result
    float[][] predictions = new float[1][10];
    outputTensor.copyTo(predictions);
    
    // Clean up
    inputTensor.close();
    outputTensor.close();
    session.close();
    model.close();
}
```

### Limitations
- Inference only (no training in Java)
- Model must be trained/exported in Python
- Performance: Slower than Python (JVM overhead)
- Limited to CPU unless GPU library installed

---

## DeepLearning4J (DL4J)

Native Java deep learning framework; no Python dependency.

### Architecture

```java
import org.deeplearning4j.nn.conf.MultiLayerConfiguration;
import org.deeplearning4j.nn.conf.NeuralNetConfiguration;
import org.deeplearning4j.nn.multilayer.MultiLayerNetwork;
import org.deeplearning4j.nn.weights.WeightInit;
import org.nd4j.linalg.activations.Activation;

// Build network configuration
MultiLayerConfiguration config = new NeuralNetConfiguration.Builder()
    .seed(12345)
    .weightInit(WeightInit.XAVIER)
    .activation(Activation.RELU)
    .updater(new Adam(0.001))
    .l2(0.0001)
    .list()
    // Layer 1: Input (784) → Hidden (256)
    .layer(0, new DenseLayer.Builder()
        .nIn(784)
        .nOut(256)
        .build())
    // Layer 2: Hidden (256) → Output (10)
    .layer(1, new OutputLayer.Builder(LossFunctions.LossFunction.NEGATIVELOGLIKELIHOOD)
        .nIn(256)
        .nOut(10)
        .activation(Activation.SOFTMAX)
        .build())
    .build();

// Create network
MultiLayerNetwork network = new MultiLayerNetwork(config);
network.init();

// Train
for (int epoch = 0; epoch < 10; epoch++) {
    network.fit(trainingData);
    double score = network.score();
    System.out.println("Epoch " + epoch + " score: " + score);
}

// Predict
INDArray testData = Nd4j.create(testImages);
INDArray predictions = network.output(testData);
```

### Advantages
- Pure Java (no Python required)
- Training & inference
- GPU support (CUDA)
- Cluster training (Spark integration)

### Disadvantages
- Smaller ecosystem than PyTorch/TensorFlow
- Fewer pre-trained models available
- Learning curve for developers from PyTorch/TensorFlow

---

## Spring AI

High-level abstraction over LLM APIs; unified interface for multiple providers.

### Spring AI Features

```
Abstracts: OpenAI, Anthropic, Google, Hugging Face
Provides: Chat, embeddings, image generation, function calling
```

### Chat API

```java
import org.springframework.ai.chat.ChatClient;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.stereotype.Service;

@Service
public class AIService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String askQuestion(String question) {
        Prompt prompt = new Prompt(new UserMessage(question));
        
        var response = chatClient.call(prompt);
        
        return response.getResult().getOutput().getContent();
    }
}
```

### Embeddings

```java
@Service
public class EmbeddingService {
    
    @Autowired
    private EmbeddingClient embeddingClient;
    
    public List<Double> embed(String text) {
        EmbeddingResponse response = embeddingClient.embedForSingle(text);
        return response.getResult().getOutput();
    }
    
    // Vector DB integration for RAG
    public void storeEmbedding(String docId, String content) {
        List<Double> embedding = embed(content);
        vectorDB.store(docId, embedding);  // Pinecone, Weaviate, etc.
    }
}
```

### Function Calling

Allow LLM to call Java methods.

```java
@Component
public class Calculator {
    
    @Description("Adds two numbers")
    public double add(
        @Parameter(description = "First number") double a,
        @Parameter(description = "Second number") double b
    ) {
        return a + b;
    }
}

// LLM can now call this function
// Prompt: "What is 5 + 3?"
// LLM recognizes → calls calculator.add(5, 3) → returns 8
```

---

## LLM API Integration

Call LLM APIs (OpenAI, Anthropic, etc.) from Java.

### OpenAI API

```java
import com.openai.api.OpenAI;
import com.openai.api.models.ChatMessage;
import com.openai.api.models.ChatCompletion;

OpenAI client = new OpenAI(apiKey);

List<ChatMessage> messages = new ArrayList<>();
messages.add(new ChatMessage("user", "Explain quantum computing"));

ChatCompletion response = client.chatCompletions.create(
    ChatCompletionRequest.builder()
        .model("gpt-4")
        .messages(messages)
        .temperature(0.7)
        .build()
);

String answer = response.choices.get(0).message.content;
System.out.println(answer);
```

### Anthropic Claude API

```java
import com.anthropic.api.Anthropic;
import com.anthropic.api.models.Message;

Anthropic client = new Anthropic(apiKey);

Message message = client.messages.create(
    MessageCreateParams.builder()
        .model("claude-3-opus-20240229")
        .maxTokens(1024)
        .messages(MessageParam.builder()
            .role(MessageParam.Role.USER)
            .content("Explain machine learning")
            .build())
        .build()
);

System.out.println(message.content.get(0).asText().text);
```

### Error Handling & Rate Limiting

```java
@Service
public class ResilientAIService {
    
    @Retryable(maxAttempts = 3, delay = 1000)
    public String callLLM(String prompt) {
        try {
            return llmClient.chat(prompt);
        } catch (RateLimitException e) {
            // Exponential backoff
            Thread.sleep(2000);
            return callLLM(prompt);  // Retry
        } catch (APIException e) {
            logger.error("API error: " + e.getMessage());
            return "Error calling LLM";
        }
    }
}
```

---

## Model Serving & Deployment

### Single Service Instance

```
┌─────────────┐
│   REST API  │
│  (Spring)   │
├─────────────┤
│ Load Model  │
│ (TensorFlow)│
├─────────────┤
│  Inference  │
│  (CPU/GPU)  │
└─────────────┘
```

### Scaled Deployment

```
                    ┌─────────────┐
                    │ API Gateway │
                    └────┬────┬───┘
                         │    │
            ┌────────────┘    └──────────┐
            │                            │
       ┌────▼────┐                 ┌────▼────┐
       │ Service1 │                 │ Service2 │
       │ (Model A)│                 │ (Model B)│
       └──────────┘                 └──────────┘

Benefits: Load balancing, failover, A/B testing
```

### Model Serving Frameworks

| Framework | Type | Pros | Cons |
|-----------|------|------|------|
| **TensorFlow Serving** | Dedicated service | Production-grade, fast | Separate infrastructure |
| **TorchServe** | PyTorch server | Native PyTorch | Limited Java support |
| **Triton Inference Server** | Multi-framework | Optimized, batching | Complex setup |
| **Spring Boot + TF/DL4J** | Embedded | Simple, single service | Less optimized |

### Docker Deployment

```dockerfile
FROM openjdk:11
WORKDIR /app
COPY model.pb .
COPY ai-service.jar .
EXPOSE 8080
CMD ["java", "-jar", "ai-service.jar"]
```

```bash
# Build & push
docker build -t myregistry/ai-service:1.0 .
docker push myregistry/ai-service:1.0

# Deploy to Kubernetes
kubectl apply -f deployment.yaml
```

---

## Production Considerations

### Latency
- Model inference latency: 50-500ms (depends on model size)
- API overhead: 10-50ms (network, serialization)
- Caching: Cache embeddings, frequent queries

### Scalability
- Horizontal: Load balance across instances
- Vertical: GPU acceleration for complex models
- Batching: Process multiple requests together (throughput vs latency)

### Cost
- API calls: ~$0.001-0.01 per 1000 tokens (OpenAI)
- GPU: $0.5-2 per hour (cloud providers)
- Storage: Vector DB, model files

### Monitoring
- Model performance: Accuracy, latency, throughput
- System health: CPU, memory, error rates
- User impact: Query success rate, response quality

```java
@Aspect
@Component
public class AIMetricsAspect {
    
    @Before("@annotation(AIMetric)")
    public void recordMetric(JoinPoint joinPoint) {
        long startTime = System.currentTimeMillis();
        // ... method execution ...
        long duration = System.currentTimeMillis() - startTime;
        metrics.recordLatency(duration);
        metrics.recordModelInference(modelName, success);
    }
}
```

---

## Interview Talking Points

- **TensorFlow vs DL4J?** TensorFlow: inference only, Python training; DL4J: pure Java, training & inference
- **Training vs Inference?** Training: data scientist in Python (slow); Inference: Java app (fast, production)
- **Spring AI benefit?** Unified interface over multiple LLM APIs; easier to switch providers
- **LLM API integration?** Call OpenAI/Anthropic/Google from Java; handle rate limits, retries
- **Model deployment?** Single service (simple), load-balanced instances (scale), or dedicated serving (optimized)
- **Latency considerations?** Model inference + network overhead; cache when possible, batch requests
- **Vector DB in Java?** Use client libraries (Pinecone SDK, Weaviate Java) for RAG pipelines
- **Cost optimization?** Batch inference, cache results, use smaller models, monitor API usage

---

**See also:** [ML Fundamentals](fundamentals.md), [Deep Learning](deep-learning.md), [RAG & Generative AI](rag-generative.md)
