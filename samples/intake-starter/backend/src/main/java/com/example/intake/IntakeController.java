package com.example.intake;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Clients describe what they want built; each intake gets a reference like INT-1001. */
@RestController
@RequestMapping("/api/intakes")
public class IntakeController {

    static final List<String> PROJECT_TYPES = List.of("ECOMMERCE", "WEBSITE", "API");
    static final int MIN_DESCRIPTION = 20;

    public record IntakeRequest(String clientName, String projectType, String description) {}

    public record Intake(String reference, String clientName, String projectType, String description, String status) {}

    private final Map<String, Intake> intakes = new ConcurrentHashMap<>();
    private final AtomicInteger next = new AtomicInteger(1001);

    @PostMapping
    public ResponseEntity<?> submit(@RequestBody IntakeRequest req) {
        if (req.clientName() == null || req.clientName().isBlank()) {
            return error("Enter your name");
        }
        if (req.projectType() == null || !PROJECT_TYPES.contains(req.projectType())) {
            return error("Choose a project type: E-commerce, Website or API");
        }
        if (req.description() == null || req.description().strip().length() < MIN_DESCRIPTION) {
            return error("Describe what you want in at least 20 characters");
        }
        String ref = "INT-" + next.getAndIncrement();
        Intake intake = new Intake(ref, req.clientName().strip(), req.projectType(), req.description().strip(), "RECEIVED");
        intakes.put(ref, intake);
        return ResponseEntity.status(HttpStatus.CREATED).body(intake);
    }

    @GetMapping("/{reference}")
    public ResponseEntity<?> get(@PathVariable String reference) {
        Intake intake = intakes.get(reference);
        return intake == null
                ? ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "No intake " + reference))
                : ResponseEntity.ok(intake);
    }

    private static ResponseEntity<Map<String, String>> error(String message) {
        return ResponseEntity.badRequest().body(Map.of("error", message));
    }
}
