# RabbitMQ

RabbitMQ is a message broker that implements AMQP 0-9-1 (and supports other protocols through plugins). Producers publish to exchanges, exchanges route messages to queues based on bindings, and consumers take messages from queues and acknowledge them. Interviewers ask about RabbitMQ to see whether you can design routing, handle failures with acknowledgements and dead-letter exchanges, and choose it over a log-based system when routing flexibility matters more than replay.

## Core concepts

### The AMQP model

- **Producer**: publishes a message to an exchange, with a routing key.
- **Exchange**: receives messages and routes them to queues. It does not store messages.
- **Binding**: a rule that links an exchange to a queue, optionally with a binding key or pattern.
- **Queue**: stores messages until a consumer takes and acknowledges them.
- **Consumer**: reads from a queue.

Messages are removed from the queue when acknowledged. That is the key difference from Kafka, where messages stay in the log for the retention period.

### Exchange types

| Type | Routing rule |
|---|---|
| Direct | Routing key must equal the binding key exactly |
| Topic | Routing key matches a binding pattern with `*` (one word) and `#` (zero or more words) |
| Fanout | Copies to every bound queue, ignoring the routing key |
| Headers | Matches on message header values rather than the routing key |

A topic exchange with `order.created.#` delivers `order.created.eu` and `order.created.eu.priority` to the bound queue, but not `order.shipped.eu`.

### Message TTL and queue limits

A per-queue TTL (`x-message-ttl`) expires messages that sit too long, and `x-max-length` limits queue depth. When a queue is full, the broker drops from the head or rejects new messages, depending on configuration. Plan these limits; an unbounded queue hides a consumer that has stopped working until memory runs out.

### Acknowledgements and nack

- **Auto-ack**: the broker considers a message delivered as soon as it is sent. A consumer crash loses it.
- **Manual ack**: the consumer acknowledges after processing. If the consumer dies first, the broker redelivers.
- **Nack / reject**: the consumer refuses a message. With `requeue=true` it goes back to the queue (and can loop forever on a poison message); with `requeue=false` it is dropped, or routed to a dead-letter exchange if one is configured.

Limit prefetch (QoS) so one slow consumer does not hold too many unacknowledged messages.

### Dead-letter exchanges

A dead-letter exchange (DLX) receives messages that are rejected without requeue, expire by TTL, or overflow a queue. Set it per queue with the `x-dead-letter-exchange` argument. Dead-letter queues then hold failed messages for inspection or replay.

### Publisher confirms and returns

Publisher confirms let the producer know the broker accepted a message. Without them, a publish can be lost if the broker fails before persisting. Spring AMQP supports correlated confirms through `spring.rabbitmq.publisher-confirm-type=correlated`.

### RPC over RabbitMQ

RPC uses a request queue and a reply queue. The client sets `reply-to` and a `correlation-id`, the server responds to the reply queue, and the client matches responses by correlation ID. It works, but synchronous RPC over a broker adds latency and coupling; prefer HTTP or gRPC for request-response unless you need the broker's routing and buffering.

### Spring AMQP

Declare exchanges, queues, and bindings as beans, and the `RabbitAdmin` creates them on startup.

```java
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class RabbitTopology {

    static final String EXCHANGE = "orders.exchange";
    static final String DLX = "orders.dlx";
    static final String QUEUE = "billing.orders";

    @Bean
    TopicExchange ordersExchange() {
        return new TopicExchange(EXCHANGE);
    }

    @Bean
    TopicExchange deadLetterExchange() {
        return new TopicExchange(DLX);
    }

    @Bean
    Queue billingQueue() {
        return QueueBuilder.durable(QUEUE)
                .withArgument("x-dead-letter-exchange", DLX)
                .build();
    }

    @Bean
    Binding billingBinding(Queue billingQueue, TopicExchange ordersExchange) {
        return BindingBuilder.bind(billingQueue).to(ordersExchange).with("order.created.#");
    }
}
```

`RabbitTemplate` publishes, and `@RabbitListener` consumes.

```java
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

@Service
class OrderPublisher {

    private final RabbitTemplate rabbit;

    OrderPublisher(RabbitTemplate rabbit) {
        this.rabbit = rabbit;
    }

    void created(String region, String payloadJson) {
        rabbit.convertAndSend(RabbitTopology.EXCHANGE, "order.created." + region, payloadJson);
    }
}
```

```java
import org.springframework.amqp.AmqpRejectAndDontRequeueException;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Component
class BillingListener {

    @RabbitListener(queues = RabbitTopology.QUEUE)
    void handle(String payloadJson) {
        try {
            process(payloadJson);
        } catch (IllegalArgumentException invalid) {
            // Do not requeue a message that can never succeed; send it to the DLX.
            throw new AmqpRejectAndDontRequeueException("invalid payload", invalid);
        }
    }

    private void process(String payloadJson) {
        if (payloadJson == null || payloadJson.isBlank()) {
            throw new IllegalArgumentException("empty payload");
        }
    }
}
```

For manual acknowledgements, set `spring.rabbitmq.listener.simple.acknowledge-mode=manual` and acknowledge explicitly. With the default auto mode, Spring acknowledges when the listener returns without an exception.

## How it works / Step by step

1. The producer publishes to an exchange with a routing key.
2. The exchange matches bindings and copies the message to each matching queue.
3. A consumer receives the message with a delivery tag and processes it.
4. On success, the consumer acknowledges; the broker removes the message.
5. On a rejected or expired message, the broker sends it to the DLX, if configured.

## Common pitfalls

- Auto-acknowledging work that can fail, so crashes silently drop messages.
- Requeuing a poison message, which causes a tight redelivery loop.
- Unbounded queues with no TTL or length limit, hiding an offline consumer.
- Publishing without confirms, then assuming the message was accepted.
- Using a topic exchange with overly broad patterns, which delivers messages to queues that should not get them.
- Using RabbitMQ for replay needs. Once acknowledged, messages are gone; use a log-based system or keep an archive.

!!! tip "Interview tip"
    **Q: When would you choose RabbitMQ over Kafka?**
    When you need flexible routing (topic, header, or fanout rules), per-message acknowledgement and retry semantics, and work queues where each message is processed by one consumer and then removed. Kafka suits high-throughput event logs that many consumers replay independently.

## Quick recap

- Producers publish to exchanges; bindings route messages to queues.
- Exchange types (direct, topic, fanout, headers) define the routing rules.
- Acknowledge after processing; reject without requeue to avoid poison loops.
- Dead-letter exchanges capture failed, expired, or overflowing messages.
- Publisher confirms tell the producer the broker accepted the message.

**See also:** [Apache Kafka](kafka.md) | [Event-Driven Architecture](event-driven-architecture.md) | [Integration Testing](../11-testing/integration-testing.md)
