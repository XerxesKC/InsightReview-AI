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
@TableName("comment")
@ApiModel(value="Comment对象", description="用户评论表")
public class Comment implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "主键")
    @TableId("comment_id")
    private String commentId;

        @ApiModelProperty(value = "用户 ID")
    @TableField("user_id")
    private String userId;

        @ApiModelProperty(value = "商家 ID")
    @TableField("merchant_id")
    private String merchantId;

        @ApiModelProperty(value = "评论内容")
    @TableField("comment_content")
    private String commentContent;

        @ApiModelProperty(value = "是否匿名(Y/N)")
    @TableField("is_anonymous")
    private String isAnonymous;

        @ApiModelProperty(value = "总评分（1-5）")
    @TableField("rating")
    private String rating;

        @ApiModelProperty(value = "环境评分")
    @TableField("env_score")
    private String envScore;

        @ApiModelProperty(value = "口味评分")
    @TableField("taste_score")
    private String tasteScore;

        @ApiModelProperty(value = "服务评分")
    @TableField("service_score")
    private String serviceScore;

        @ApiModelProperty(value = "审核状态（待审、通过等）")
    @TableField("status")
    private String status;

        @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

        @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;

        @ApiModelProperty(value = "是否删除")
    @TableField("is_deleted")
    private String isDeleted;

    @ApiModelProperty(value = "图片链接")
    @TableField("image")
    private String image;

    @ApiModelProperty(value = "视频链接")
    @TableField("video")
    private String video;

    @ApiModelProperty(value = "动态 ID")
    @TableField("post_id")
    private String postId;

    @TableField(exist = false)
    private String userName;
}
