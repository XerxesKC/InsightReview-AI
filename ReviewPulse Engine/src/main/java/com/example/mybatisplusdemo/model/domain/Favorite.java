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
@TableName("favorite")
@ApiModel(value="Favorite对象", description="用户收藏表")
public class Favorite implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "主键")
    @TableId("favorite_id")
    private String favoriteId;

        @ApiModelProperty(value = "用户 ID")
    @TableField("user_id")
    private String userId;

        @ApiModelProperty(value = "商家 ID")
    @TableField("merchant_id")
    private String merchantId;

        @ApiModelProperty(value = "自定义标签（如\"常去\"）")
    @TableField("tag")
    private String tag;

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
