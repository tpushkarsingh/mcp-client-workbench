package com.mcp.registry.repository;

import com.mcp.registry.model.MCPServer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface MCPServerRepository extends JpaRepository<MCPServer, UUID> {
    Optional<MCPServer> findByName(String name);
}
