package com.example.mybatisplusdemo.web.controller;

import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.domain.User;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.IAdminService;
import com.example.mybatisplusdemo.service.IMerchantService;
import com.example.mybatisplusdemo.service.ICommentService;
import com.example.mybatisplusdemo.service.IUserService;
import com.example.mybatisplusdemo.model.domain.Admin;

import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final Logger logger = LoggerFactory.getLogger(AdminController.class);

    @Autowired
    private IAdminService adminService;

    @Autowired
    private IMerchantService merchantService;

    @Autowired
    private ICommentService commentService;

    @Autowired
    private IUserService userService;

    
    @GetMapping("/{id}")
    public JsonResponse<Admin> getById(@PathVariable("id") Long id) throws Exception {
        Admin admin = adminService.getById(id);
        return JsonResponse.success(admin);
    }

    @PostMapping("/login")
    public JsonResponse<Admin> login(@RequestBody Admin admin) {
        return adminService.login(admin);
    }

    @GetMapping("/five-star-merchants")
    public JsonResponse<List<Map<String, Object>>> getFiveStarMerchants() {
        List<Map<String, Object>> merchants = merchantService.getFiveStarMerchants();
        return JsonResponse.success(merchants);
    }

    @GetMapping("/most-commented-merchants")
    public JsonResponse<List<Map<String, Object>>> getMostCommentedMerchants() {
        List<Map<String, Object>> merchants = merchantService.getMostCommentedMerchants();
        return JsonResponse.success(merchants);
    }

    @GetMapping("/highest-rated-merchants")
    public JsonResponse<List<Map<String, Object>>> getHighestRatedMerchants() {
        List<Map<String, Object>> merchants = merchantService.getHighestRatedMerchants();
        return JsonResponse.success(merchants);
    }

    @GetMapping("/rating-distribution")
    public JsonResponse<List<Map<String, Object>>> getRatingDistribution() {
        List<Map<String, Object>> distribution = merchantService.getRatingDistribution();
        return JsonResponse.success(distribution);
    }

    @GetMapping("/getInfo")
    public JsonResponse<Admin> getInfo() {
        Admin currentAdmin = SessionUtils.getCurrentAdminInfo();
        if (currentAdmin != null) {
            return JsonResponse.success(currentAdmin);
        } else {
            return JsonResponse.failure("未登录或用户信息不存在");
        }
    }


}
