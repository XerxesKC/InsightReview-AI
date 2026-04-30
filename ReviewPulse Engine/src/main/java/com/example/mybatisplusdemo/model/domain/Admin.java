package com.example.mybatisplusdemo.model.domain;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
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
@TableName("admin")
@ApiModel(value="Admin对象", description="管理员账户表")
public class Admin implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "管理员主键")
    @TableId("admin_id")
    private String adminId;

        @ApiModelProperty(value = "管理员名称")
    @TableField("admin_name")
    private String adminName;

        @ApiModelProperty(value = "管理员密码")
    @TableField("admin_password")
    private String adminPassword;

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
