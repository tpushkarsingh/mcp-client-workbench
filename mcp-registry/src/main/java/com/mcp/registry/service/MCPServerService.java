package com.mcp.registry.service;

import com.mcp.registry.model.MCPServer;
import com.mcp.registry.repository.MCPServerRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class MCPServerService {

    private final MCPServerRepository repository;

    public MCPServer registerServer(MCPServer server) {
        // Idempotency: Update if exists, else Create
        Optional<MCPServer> existing = repository.findByName(server.getName());
        if (existing.isPresent()) {
            MCPServer toUpdate = existing.get();
            toUpdate.setVersion(server.getVersion());
            toUpdate.setBinaryUrl(server.getBinaryUrl());
            toUpdate.setDescription(server.getDescription());
            toUpdate.setRuntimeConfig(server.getRuntimeConfig());
            return repository.save(toUpdate);
        }
        return repository.save(server);
    }

    public List<MCPServer> getAllServers() {
        return repository.findAll();
    }

    public Optional<MCPServer> getServerByName(String name) {
        return repository.findByName(name);
    }

    public Map<String, Object> generateMcpConfig(String name) {
        MCPServer server = repository.findByName(name)
                .orElseThrow(() -> new RuntimeException("Server not found: " + name));

        // Construct mcp.json format
        // { "servers": { "name": { "command": "...", "args": [...] } } }

        // Note: The Client needs to know HOW to run this binary.
        // We assume the Client has the 'RuntimeService' running (the Python script we
        // wrote).
        // The mcp.json generation here might be used by the Client to Auto-Configure
        // itself.

        // Current design: Client pulls Binary from Artifactory.
        // So the 'command' depends on the Client's runtime architecture.
        // This endpoint serves the *Logical* config.

        return Map.of(
                "servers", Map.of(
                        server.getName(), Map.of(
                                "command", "wasm-runtime", // Generic command, client maps this
                                "args", List.of("--url", server.getBinaryUrl()),
                                "env", server.getRuntimeConfig() != null ? server.getRuntimeConfig() : Map.of())));
    }
}
