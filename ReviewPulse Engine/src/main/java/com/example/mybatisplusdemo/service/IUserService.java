package com.example.mybatisplusdemo.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.model.domain.User;
import com.baomidou.mybatisplus.extension.service.IService;
import com.example.mybatisplusdemo.model.dto.UserInsertDTO;
import com.example.mybatisplusdemo.model.dto.UserSearchDTO;
import com.example.mybatisplusdemo.model.dto.UserUpdateDTO;

import java.util.List;


public interface IUserService extends IService<User> {

    Page<User> searchUser(Page<User> page, UserSearchDTO userSearchDTO);

    
    JsonResponse login(User user);

    
    JsonResponse insertUser(UserInsertDTO userInsertDTO);

    JsonResponse updateUser(UserUpdateDTO userUpdateDTO);

    JsonResponse updateCurrentUser(UserUpdateDTO userUpdateDTO);

    User deleteUser(String userId);

    Page<User> searchUserLike(Page<User> page, String query);

    List<User> getUsers();


}
