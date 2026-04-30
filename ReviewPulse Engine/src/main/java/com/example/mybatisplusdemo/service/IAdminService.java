package com.example.mybatisplusdemo.service;

import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.model.domain.Admin;
import com.baomidou.mybatisplus.extension.service.IService;


public interface IAdminService extends IService<Admin> {

    JsonResponse login(Admin admin);
}
