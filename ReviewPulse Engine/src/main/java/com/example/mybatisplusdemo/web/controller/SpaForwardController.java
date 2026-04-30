package com.example.mybatisplusdemo.web.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class SpaForwardController {

    @GetMapping(value = {
            "/login",
            "/register",
            "/user",
            "/user/**",
            "/merchant",
            "/merchant/**",
            "/admin",
            "/admin/**"
    })
    public String forward() {
        return "forward:/index.html";
    }
}
