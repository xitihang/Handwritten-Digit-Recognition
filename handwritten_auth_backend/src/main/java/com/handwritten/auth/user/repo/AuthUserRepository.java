package com.handwritten.auth.user.repo;

import com.handwritten.auth.user.entity.AuthUser;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthUserRepository extends JpaRepository<AuthUser, Long> {
}


