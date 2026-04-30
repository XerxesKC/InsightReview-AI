package com.example.mybatisplusdemo.web.controller;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StreamUtils;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Enumeration;

@RestController
public class AgentApiProxyController {

    private static final String AGENT_BASE_URL = "http://127.0.0.1:8001";
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

    @RequestMapping("/api/v1/**")
    public ResponseEntity<byte[]> proxy(HttpServletRequest request) throws IOException, InterruptedException {
        String query = request.getQueryString();
        String targetUrl = AGENT_BASE_URL + request.getRequestURI() + (query == null ? "" : "?" + query);

        byte[] body = StreamUtils.copyToByteArray(request.getInputStream());
        HttpRequest.BodyPublisher bodyPublisher = body.length == 0
                ? HttpRequest.BodyPublishers.noBody()
                : HttpRequest.BodyPublishers.ofByteArray(body);

        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(targetUrl))
                .timeout(Duration.ofMinutes(5))
                .method(HttpMethod.valueOf(request.getMethod()).name(), bodyPublisher);

        Enumeration<String> headerNames = request.getHeaderNames();
        while (headerNames.hasMoreElements()) {
            String headerName = headerNames.nextElement();
            if ("host".equalsIgnoreCase(headerName) || "content-length".equalsIgnoreCase(headerName)) {
                continue;
            }
            Enumeration<String> headerValues = request.getHeaders(headerName);
            while (headerValues.hasMoreElements()) {
                builder.header(headerName, headerValues.nextElement());
            }
        }

        HttpResponse<byte[]> response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofByteArray());

        HttpHeaders headers = new HttpHeaders();
        response.headers().map().forEach((name, values) -> {
            if (!"transfer-encoding".equalsIgnoreCase(name)) {
                headers.put(name, values);
            }
        });

        return ResponseEntity
                .status(response.statusCode())
                .headers(headers)
                .body(response.body());
    }
}
