# LLM Integration

A large language model (LLM) generates text from a sequence of input messages. Interviewers ask about LLM integration to see whether you can call a model as a dependency: manage its inputs and outputs, control cost and latency, and handle the ways it fails. The examples here use a provider-neutral interface, because the concepts apply to any hosted or self-hosted model.

## Core concepts

### Models as remote dependencies

Treat a model like any other external service. It has latency, rate limits, timeouts, costs, outages, and output that varies between calls. Wrap it behind an interface in your code, so the rest of the application does not depend on one vendor's SDK. That also lets you test with a fake model and switch providers without touching business logic.

Providers include hosted APIs from several companies and open-weight models that you can run yourself. Compare them on the criteria your product needs (quality on your tasks, data handling terms, latency, cost, deployment constraints) and measure on your own examples rather than relying on general claims.

### A provider-neutral interface

A minimal shape for a chat-style call:

```java
import java.util.List;

public class LlmClientDemo {

    public enum Role { SYSTEM, USER, ASSISTANT }

    public record ChatMessage(Role role, String content) {}

    public record SamplingOptions(double temperature, double topP, int maxOutputTokens) {}

    public interface ChatModel {
        String complete(List<ChatMessage> messages, SamplingOptions options);
    }

    // A fake model for unit tests: no network, deterministic output
    static class EchoModel implements ChatModel {
        @Override
        public String complete(List<ChatMessage> messages, SamplingOptions options) {
            return "echo: " + messages.get(messages.size() - 1).content();
        }
    }

    public static void main(String[] args) {
        ChatModel model = new EchoModel();
        String answer = model.complete(
                List.of(new ChatMessage(Role.SYSTEM, "Be brief."),
                        new ChatMessage(Role.USER, "Summarise this order.")),
                new SamplingOptions(0.2, 0.9, 256));
        System.out.println(answer);
    }
}
```

Each real provider implementation would map these records to its own request format. Your business code only sees `ChatModel`.

### Prompt design and roles

A prompt is the full set of messages sent to the model. Most chat APIs use roles:

- **System:** standing instructions about behaviour, format, and limits
- **User:** the request or question from the end user, or your application's input
- **Assistant:** previous model replies, included when you need multi-turn context

Good prompts are specific about the task, the output format, and what to do when information is missing. Keep untrusted content (user text, retrieved documents) clearly delimited, and say that instructions inside it must not be followed. This reduces, but does not eliminate, **prompt injection**, where input text tries to override your instructions.

### Context window and token limits

A model reads at most a fixed number of **tokens** in one call, its context window. Tokens are sub-word pieces, not words or characters, and the count depends on the model's tokeniser. The window must hold the system prompt, the conversation so far, retrieved context, and the output. If the input is too long, the call fails or you must truncate.

Practical handling:

1. Count input tokens with the tokeniser for your model, not with a rough character ratio.
2. Reserve room for the output (`maxOutputTokens`).
3. Drop or summarise the oldest conversation turns first, and keep the system prompt.
4. Reject or split requests that cannot fit.

### Cost control

Cost usually scales with input and output tokens. Controls to design in:

- Cap `maxOutputTokens` for each use case
- Trim context to what the task needs (see [RAG](rag-and-vector-databases.md))
- Cache responses for repeated identical requests where the answer is stable
- Send simple tasks to cheaper models and reserve larger models for hard ones
- Record usage per request and per tenant, so spikes are visible and attributable
- Set budgets and alerts (see [observability](../20-observability/alerting-health-checks.md))

Do not hard-code prices in your code or docs. They change, and they differ between providers and models.

### Sampling parameters

Sampling parameters control how the model picks each next token:

- **Temperature:** higher values make output more varied; lower values make it more deterministic. Near zero suits extraction and classification. Higher values suit brainstorming.
- **Top-k:** consider only the k most likely next tokens.
- **Top-p (nucleus sampling):** consider the smallest set of tokens whose cumulative probability reaches p.

Not every provider exposes all of these, and some ignore parameters for certain models. Set them explicitly, test the effect on your data, and do not assume determinism even at temperature zero.

### Streaming responses

A long answer can take seconds. **Streaming** sends tokens as they are generated, so the user sees output sooner. On the server, that means forwarding chunks over Server-Sent Events or a WebSocket, and handling client disconnects by cancelling the upstream call to save cost. Streaming changes error handling: the HTTP status is already sent when a failure happens mid-stream, so you need an in-band error event.

### Function (tool) calling

Tool calling lets the model request an action from your code. You describe available functions with names, descriptions, and JSON-schema parameters. The model replies with a structured call, such as `lookupOrder` with `{"orderId": "42"}`. Your code validates the arguments, runs the function, and returns the result to the model, which then writes its answer.

Important rules:

- The model proposes; your code decides. Validate and authorise every call as you would any client request.
- Limit which tools exist for a given user and request.
- Cap the number of tool-call rounds to prevent loops.
- Treat tool output as data, not as instructions.

### Structured output

When you need data rather than prose, ask for JSON that matches a schema, then parse and validate it. Models can still produce invalid output, so always validate with a schema or a typed parser and retry or fall back on failure.

### Failure handling

Expect timeouts, rate-limit responses, content filtering, and malformed output. Design for them:

- Set explicit timeouts for every call.
- Retry transient errors with exponential backoff and jitter, within a bounded budget.
- Validate outputs and treat invalid ones as failures.
- Provide a fallback (cached answer, simpler path, or a clear "unavailable" message).
- Log request metadata and outcomes, but do not log full prompts containing personal data unless you have a retention policy for them.

## How it works

1. The application builds a prompt from a system instruction, the user's input, and any retrieved context.
2. It counts tokens, checks the window, and sets sampling and output limits.
3. It calls the model through the provider adapter, with a timeout.
4. If the model requests a tool, the application validates the call, runs it, and sends the result back.
5. The response is validated, logged with usage data, and returned, or streamed to the client.

## Common pitfalls

- Coupling business code to one vendor's SDK and types
- Estimating tokens with a character ratio and overflowing the window in production
- No timeout, so one slow call ties up a thread or connection
- Trusting model output without validation, especially when it drives actions
- Letting retrieved documents or user text override system instructions
- Logging full prompts, which can contain personal data
- Assuming temperature zero gives identical output every time

!!! tip "Interview tip"
    **Q: How would you keep an LLM feature from running up costs or hanging the service?**
    A: Put the model behind an interface with timeouts and bounded retries. Cap input and output tokens, trim context, and record usage per tenant with alerts. Validate every output, cap tool-call rounds, and provide a fallback when the call fails. Measure cost and latency on real traffic rather than guessing.

## Quick recap

- Wrap the model behind your own interface so you can test and switch providers
- Manage the context window explicitly; count tokens with the model's tokeniser
- Sampling parameters shape output; set them and test their effect
- Tool calls are proposals: validate, authorise, and bound them
- Plan for timeouts, retries, invalid output, and cost from the start

**See also:** [RAG and Vector Databases](rag-and-vector-databases.md), [Spring AI and Use Cases](spring-ai-use-cases.md)
