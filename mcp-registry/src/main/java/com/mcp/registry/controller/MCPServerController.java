package com.mcp.registry.controller;

import com.mcp.registry.model.MCPServer;
import com.mcp.registry.service.MCPServerService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/servers")
@RequiredArgsConstructor
public class MCPServerController {

    private final MCPServerService service;

    @PostMapping
    public ResponseEntity<MCPServer> register(@RequestBody MCPServer server) {
        return ResponseEntity.ok(service.registerServer(server));
    }

    @GetMapping
    public ResponseEntity<List<MCPServer>> list() {
        return ResponseEntity.ok(service.getAllServers());
    }

    @GetMapping("/{name}")
    public ResponseEntity<MCPServer> get(@PathVariable String name) {
        return service.getServerByName(name)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{name}/mcp.json")
    public ResponseEntity<Map<String, Object>> getMcpJson(@PathVariable String name) {
        try {
            return ResponseEntity.ok(service.generateMcpConfig(name));
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        }
    }
}
