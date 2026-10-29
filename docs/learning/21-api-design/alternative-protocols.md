# Alternative Protocols: GraphQL, gRPC, and WebSockets

REST over HTTP is the default, but other styles fit some problems better. Interviewers ask about these to check that you can choose a protocol for a reason, not out of habit. Know what each one optimises for and what it costs.

## Core concepts

### REST as the baseline

REST works well for public APIs, cacheable reads, and simple resource operations. Its weak points are over-fetching (a screen needs three fields but gets thirty), under-fetching (a screen needs three resources and makes three round trips), and a lack of a standard way to push data from the server. The protocols below address different parts of that list.

### GraphQL: queries, mutations, and subscriptions

**GraphQL** exposes a single endpoint with a typed schema. The client asks for exactly the fields it needs, and can ask for related data in one request. There are three operation types:

- **Query:** read data
- **Mutation:** change data
- **Subscription:** receive pushed updates, usually over a WebSocket-based transport

Schema definition uses SDL (Schema Definition Language):

```graphql
type Query {
  order(id: ID!): Order
}

type Mutation {
  placeOrder(input: PlaceOrderInput!): Order!
}

type Subscription {
  orderStatusChanged(id: ID!): Order!
}

type Order {
  id: ID!
  status: String!
  items: [OrderItem!]!
}

type OrderItem {
  sku: String!
  quantity: Int!
}

input PlaceOrderInput {
  sku: String!
  quantity: Int!
}
```

Trade-offs to know:

- Caching is harder than for REST, because every request goes to the same URL and the body decides the operation. Caching moves into the resolvers or into persisted queries.
- Clients can send expensive queries, so you need depth limits, complexity limits, and timeouts.
- The **N+1 problem** appears when a list resolver loads a related record once per item. Batching loaders (such as the DataLoader pattern) group those lookups.
- Errors are returned in the response body alongside partial data, not through status codes alone.

### gRPC: Protocol Buffers over HTTP/2

**gRPC** is a remote procedure call framework. You define services and messages in a `.proto` file using **Protocol Buffers** (protobuf), and tooling generates client and server code. Messages are compact binary, and gRPC runs over **HTTP/2**, which multiplexes many calls over one connection and supports streaming.

```proto
syntax = "proto3";

package orders.v1;

service OrderService {
  rpc GetOrder (GetOrderRequest) returns (OrderReply);
  rpc WatchOrder (GetOrderRequest) returns (stream OrderReply);
}

message GetOrderRequest {
  int64 id = 1;
}

message OrderReply {
  int64 id = 1;
  string status = 2;
}
```

Streaming modes are unary (one request, one response), server streaming (one request, many responses), client streaming, and bidirectional. Field numbers (`= 1`, `= 2`) are part of the wire format, so never reuse a number once it has been released.

Use gRPC for service-to-service calls inside your platform, where you control both ends and want strong typing and efficient payloads. Browsers cannot call gRPC directly without a proxy (gRPC-Web), so REST or GraphQL usually remains the public-facing choice.

### WebSockets: persistent bidirectional connections

A **WebSocket** starts as an HTTP request, then upgrades to a long-lived connection where either side can send messages at any time. This suits chat, live dashboards, and notifications.

With Spring, a text handler looks like this:

```java
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;

public class NotificationHandler extends TextWebSocketHandler {

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws IOException {
        // Echo an acknowledgement back on the same connection
        session.sendMessage(new TextMessage("ack: " + message.getPayload()));
    }
}
```

Connection management is the hard part:

- **Lifecycle:** handle connect, disconnect, and errors. Clients drop connections on mobile networks all the time.
- **Heartbeats:** send periodic pings so dead connections are detected.
- **Reconnection:** clients reconnect with backoff, and resume from the last event they saw, not from scratch.
- **Scaling:** a connection is tied to one server instance. Broadcasts across instances need a shared channel such as a message broker or pub/sub.
- **Authentication:** check the credentials at the handshake, and re-check authorisation for each subscription.

### HTTP/2 and HTTP/3 in brief

HTTP/2 multiplexes requests over one connection and compresses headers. HTTP/3 runs over QUIC. Both matter for performance, and gRPC depends on HTTP/2. You rarely configure them in application code, but know that they change connection costs.

### Choosing

| Need | Good fit | Why |
|---|---|---|
| Public, cacheable, resource-oriented API | REST | Standard tooling, HTTP caches |
| Many clients with differing data needs | GraphQL | Clients shape responses |
| Internal service calls, high throughput | gRPC | Typed contracts, binary, streaming |
| Server pushes live updates both ways | WebSockets | Persistent bidirectional channel |
| Server pushes one-way updates | Server-Sent Events | Simpler than WebSockets for this case |

## How it works

1. **REST:** a client sends a request to a resource URL and gets a representation.
2. **GraphQL:** a client posts a query to one endpoint; the server resolves each requested field.
3. **gRPC:** a generated stub serialises the request to protobuf and calls the server over HTTP/2.
4. **WebSocket:** the client upgrades an HTTP connection once, then both sides exchange frames until either closes it.

## Common pitfalls

- Picking GraphQL or gRPC because they are newer, without a problem they solve
- Exposing an unbounded GraphQL query surface, with no depth or cost limits
- Reusing or renumbering protobuf field numbers, which breaks existing clients
- Holding WebSocket connections without heartbeats, so dead connections accumulate
- Broadcasting from one instance only, so clients on other instances miss messages
- Forgetting that gRPC is not directly callable from a browser

!!! tip "Interview tip"
    **Q: When would you use gRPC instead of REST?**
    A: For internal service-to-service calls where both sides are under your control and you want typed contracts, compact binary messages, and streaming over HTTP/2. I would keep REST for public APIs, because it is easy to cache, test with a browser or curl, and is understood by any client.

## Quick recap

- GraphQL lets clients shape responses; guard it with depth and cost limits and fix N+1 with batching
- gRPC uses protobuf over HTTP/2 with streaming; never reuse field numbers
- WebSockets give persistent two-way channels; handle heartbeats, reconnects, and multi-instance fan-out
- REST remains the default for public and cacheable APIs
- Choose by need, and say why

**See also:** [REST Principles and Versioning](rest-principles-versioning.md), [Pagination, Errors, and Idempotency](pagination-errors-idempotency.md), [API Security](api-security.md)
