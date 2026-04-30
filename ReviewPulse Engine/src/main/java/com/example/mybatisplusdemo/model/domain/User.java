package com.example.mybatisplusdemo.model.domain;

import com.baomidou.mybatisplus.annotation.*;
import com.baomidou.mybatisplus.annotation.TableId;

import java.io.Serializable;
import java.time.LocalDateTime;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;


@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("user")
@ApiModel(value="User对象", description="用户信息表")
public class User implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "用户主键")
    @TableId(value = "user_id", type = IdType.ASSIGN_ID)
    private String userId;

        @ApiModelProperty(value = "昵称")
    @TableField("user_name")
    private String userName;

        @ApiModelProperty(value = "手机号（可选）")
    @TableField("phone")
    private String phone;

        @ApiModelProperty(value = "邮箱（可选）")
    @TableField("email")
    private String email;

        @ApiModelProperty(value = "密码")
    @TableField("password")
    private String password;

        @ApiModelProperty(value = "头像 URL")
    @TableField("avatar")
    private String avatar;

        @ApiModelProperty(value = "性别（F/M/O）")
    @TableField("gender")
    private String gender;

        @ApiModelProperty(value = "出生日期（字符串格式）")
    @TableField("birthday")
    private String birthday;

        @ApiModelProperty(value = "是否公开收藏（T/F）")
    @TableField("show_collection")
    private String showCollection;

        @ApiModelProperty(value = "是否公开评论（T/F）")
    @TableField("show_comment")
    private String showComment;

        @ApiModelProperty(value = "账号状态")
    @TableField("user_status")
    private String userStatus;

    @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

        @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;

        @ApiModelProperty(value = "是否删除")
    @TableField("is_deleted")
    private String isDeleted;


}
