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
@TableName("category")
@ApiModel(value="Category对象", description="商家分类表")
public class Category implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "类别 ID")
    @TableId("category_id")
    private String categoryId;

        @ApiModelProperty(value = "类别名称")
    @TableField("category_name")
    private String categoryName;

        @ApiModelProperty(value = "父类别 ID（可为 null）")
    @TableField("parent_id")
    private String parentId;

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
