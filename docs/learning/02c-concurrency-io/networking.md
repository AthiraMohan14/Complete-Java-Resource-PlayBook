# Networking in Java

Networking code connects Java programs to other machines over TCP and HTTP. Interviewers ask about these APIs to check whether you know the difference between low-level sockets and high-level HTTP clients, and how to handle timeouts, streams, and email delivery in a service.

## Core concepts

### Networking basics

Most application traffic uses TCP (reliable, ordered byte streams) or UDP (unreliable datagrams). Each endpoint is identified by an IP address and a port number. HTTP runs on top of TCP. Java offers several layers, from raw sockets up to a full HTTP client.

| Layer | Class or package | Use |
|---|---|---|
| Addresses | `java.net.InetAddress` | Resolve names and inspect addresses |
| URLs | `java.net.URL`, `URI` | Parse and build locations |
| Raw TCP | `java.net.Socket`, `ServerSocket` | Custom protocols |
| HTTP (current) | `java.net.http.HttpClient` (Java 11+) | Call REST APIs |
| HTTP (legacy) | `HttpURLConnection` | Maintenance of old code only |

### InetAddress

`InetAddress` represents an IP address and can resolve a host name through DNS.

```java
import java.net.InetAddress;
import java.net.UnknownHostException;

public class ResolveHost {
    public static void main(String[] args) throws UnknownHostException {
        InetAddress addr = InetAddress.getByName("localhost");
        System.out.println(addr.getHostAddress());   // typically 127.0.0.1
        System.out.println(addr.isLoopbackAddress()); // true
    }
}
```

`getByName` may block on DNS. Its failure mode is `UnknownHostException`, which is a checked exception, so handle it.

### URL and URI

`URI` is the modern parser for the general syntax (RFC 3986), and it does not require a network connection. `URL` is older and can open a connection, but it does not handle all URI forms well. Prefer `URI` to parse and build addresses, and convert with `toURL()` only when an API needs a `URL`.

```java
import java.net.URI;

public class UriParts {
    public static void main(String[] args) {
        URI uri = URI.create("https://example.com/search?q=java");
        System.out.println(uri.getHost());   // example.com
        System.out.println(uri.getQuery());  // q=java
    }
}
```

`URLConnection` is the legacy way to read a resource through a `URL`. It works, but for HTTP calls use `HttpClient`.

### HttpClient (Java 11+)

`java.net.http.HttpClient` is the standard HTTP client. It supports HTTP/1.1 and HTTP/2, synchronous and asynchronous calls, and request timeouts. It replaces `HttpURLConnection` for new code.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class HttpDemo {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://example.com/"))
                .timeout(Duration.ofSeconds(10))
                .GET()
                .build();

        HttpResponse<String> response =
                client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println(response.statusCode());
    }
}
```

Asynchronous call, which returns a `CompletableFuture` (see [Executors and Futures](executors-futures.md)):

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class AsyncFetch {
    public static void main(String[] args) {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://example.com")).build();
        client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
              .thenApply(HttpResponse::body)
              .thenAccept(System.out::println)
              .join();
    }
}
```

Points to remember:

- Reuse one `HttpClient` across requests. It manages connections and a thread pool internally.
- Set both a connect timeout (on the client) and a request timeout (on the request). Without them, a stuck server can hold threads forever.
- `send` throws `IOException` and `InterruptedException`. Check the status code: a non-2xx response is not an exception.
- Body handlers choose how to read the response. `ofString()` loads everything into memory. Use `ofInputStream()` or `ofFile(path)` for large bodies.

### Sockets: client-server communication

A `ServerSocket` listens on a port and returns a `Socket` for each connection. A `Socket` gives you an input stream and an output stream. The simplest server handles one client at a time.

```java
import java.io.*;
import java.net.*;

public class EchoServer {
    public static void main(String[] args) throws IOException {
        try (ServerSocket server = new ServerSocket(5000);
             Socket client = server.accept();
             BufferedReader in = new BufferedReader(
                     new InputStreamReader(client.getInputStream()));
             PrintWriter out = new PrintWriter(client.getOutputStream(), true)) {

            String line;
            while ((line = in.readLine()) != null) {
                out.println("echo: " + line);
            }
        }
    }
}
```

A matching client:

```java
import java.io.*;
import java.net.Socket;

public class EchoClient {
    public static void main(String[] args) throws IOException {
        try (Socket socket = new Socket("localhost", 5000);
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(
                     new InputStreamReader(socket.getInputStream()))) {

            out.println("hello");
            System.out.println(in.readLine());   // echo: hello
        }
    }
}
```

Notes on sockets:

- `readLine()` returns `null` when the peer closes the connection. Always handle it.
- `PrintWriter` with `autoFlush` set to `true` flushes after `println`. Without it, messages can sit in the buffer.
- For many clients, run each connection on an executor (or a virtual thread on Java 21) instead of handling them in the accept loop.
- `socket.setSoTimeout(ms)` makes a blocking read give up after the timeout by throwing `SocketTimeoutException`.

### NIO channels for networking

`java.nio.channels` provides non-blocking socket channels driven by a `Selector`. One thread can watch many connections. This is the model behind many high-throughput servers, but it is more complex than blocking sockets. Frameworks such as Netty wrap it. Mention it in interviews, but use blocking I/O or `HttpClient` unless you need the extra throughput.

### Sending email with Jakarta Mail

Sending email from Java uses the Jakarta Mail API (formerly JavaMail). In Jakarta EE 9 and later, the packages moved from `javax.mail` to `jakarta.mail`. Check your dependency: older code uses `javax.mail`, and new code uses `jakarta.mail`. The API jar alone cannot send mail, so add a compatible Jakarta Mail implementation as a runtime dependency, and check the version against your Jakarta EE release.

```java
import jakarta.mail.*;
import jakarta.mail.internet.*;
import java.util.Properties;

public class MailSender {
    public static void send(String host, String from, String to, String body)
            throws MessagingException {
        Properties props = new Properties();
        props.put("mail.smtp.host", host);
        props.put("mail.smtp.port", "587");
        props.put("mail.smtp.starttls.enable", "true");

        Session session = Session.getInstance(props, new Authenticator() {
            @Override
            protected PasswordAuthentication getPasswordAuthentication() {
                return new PasswordAuthentication(
                        System.getenv("MAIL_USER"), System.getenv("MAIL_PASSWORD"));
            }
        });

        Message msg = new MimeMessage(session);
        msg.setFrom(new InternetAddress(from));
        msg.setRecipients(Message.RecipientType.TO, InternetAddress.parse(to));
        msg.setSubject("Status update");
        msg.setText(body);
        Transport.send(msg);
    }
}
```

Credentials come from environment variables, never from source code. Real services usually send mail through a transactional provider or an authenticated SMTP relay, and they use a queue so a slow mail server does not block a web request.

## How it works / Step by step

1. Parse the target with `URI`, and resolve the host with `InetAddress` if you need the address.
2. For HTTP, build an `HttpRequest` with a timeout, send it through a shared `HttpClient`, and read the status and body.
3. For a custom protocol, open a `Socket`, write to its output stream, and read from its input stream.
4. Close connections in try-with-resources, and treat `null` from `readLine()` as end of stream.
5. For email, open a `Session` with SMTP settings, build a `MimeMessage`, and call `Transport.send`.

## Common pitfalls

- Creating a new `HttpClient` for every request, which wastes connections and threads.
- Leaving out timeouts, so one slow server stalls the whole service.
- Treating a 4xx or 5xx response as an exception. `HttpClient` returns it normally.
- Reading an unbounded response body into a `String`.
- Forgetting `autoFlush` on a `PrintWriter` over a socket.
- Mixing `javax.mail` and `jakarta.mail` classes in the same project.
- Hard-coding mail or API credentials in source code.
- Using `HttpURLConnection` in new code.

!!! tip "Interview tip"
    **Q: How would you call a REST API from Java 17 without third-party libraries?**
    Use `java.net.http.HttpClient`. Build one shared client with a connect timeout, build each `HttpRequest` with a request timeout, send it with `send` or `sendAsync`, and check the status code yourself. Mention that `HttpURLConnection` is legacy.

## Quick recap

- `InetAddress` resolves names. `URI` parses addresses without a network call.
- `HttpClient` (Java 11+) is the standard HTTP client, with sync and async calls.
- Always set connect and request timeouts. Reuse one client.
- `ServerSocket` and `Socket` give you raw TCP streams. Close them with try-with-resources.
- Jakarta Mail uses `jakarta.mail` in Jakarta EE 9 and later. Keep credentials out of code.

**See also:** [I/O, Files, and Serialisation](io-files-serialisation.md), [Executors and Futures](executors-futures.md), [Threads Basics](threads-basics.md)
