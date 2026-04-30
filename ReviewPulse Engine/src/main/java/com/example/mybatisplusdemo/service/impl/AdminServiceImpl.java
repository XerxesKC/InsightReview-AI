package com.example.mybatisplusdemo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.model.domain.Admin;
import com.example.mybatisplusdemo.mapper.AdminMapper;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.service.IAdminService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;


@Service
public class AdminServiceImpl extends ServiceImpl<AdminMapper, Admin> implements IAdminService {

    @Autowired AdminMapper adminMapper;

    @Override
    public JsonResponse login(Admin admin) {
        LambdaQueryWrapper<Admin> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(Admin::getAdminName, admin.getAdminName())
                .eq(Admin::getAdminPassword, admin.getAdminPassword());
        Admin currentAdmin = adminMapper.selectOne(queryWrapper);

        if (currentAdmin == null) {
            return JsonResponse.failure("用户不存在或密码错误");
        }
        SessionUtils.saveCurrentAdminInfo(currentAdmin);;
        return JsonResponse.success(currentAdmin, "登录成功");
    }
}
