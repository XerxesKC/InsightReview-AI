package com.example.mybatisplusdemo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.domain.User;
import com.example.mybatisplusdemo.model.dto.UserSearchDTO;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;


public interface UserMapper extends BaseMapper<User> {

    Page<User> selectUserPage(@Param("page") Page<User> page, @Param("dto") UserSearchDTO userDTO);

    List<User> getUsers();


}
