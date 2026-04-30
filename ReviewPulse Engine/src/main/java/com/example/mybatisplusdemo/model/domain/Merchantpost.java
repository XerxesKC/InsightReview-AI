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
@TableName("merchantpost")
@ApiModel(value="Merchantpost对象", description="商家动态表")
public class Merchantpost implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "动态ID")
    @TableId(type = IdType.ASSIGN_UUID)
    @TableField("post_id")
    private String postId;

        @ApiModelProperty(value = "商家ID")
    @TableField("merchant_id")
    private String merchantId;

        @ApiModelProperty(value = "标题")
    @TableField("title")
    private String title;

        @ApiModelProperty(value = "内容")
    @TableField("content")
    private String content;

        @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

        @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;

        @ApiModelProperty(value = "是否删除")
    @TableField("is_deleted")
    private String isDeleted;

        @ApiModelProperty(value = "图片URL")
    @TableField("image_url")
    private String imageUrl;

        @ApiModelProperty(value = "视频URL")
    @TableField("video_url")
    private String videoUrl;

        @ApiModelProperty(value = "点赞数")
    @TableField("like_count")
    private String likeCount;

        @ApiModelProperty(value = "评论数")
    @TableField("comment_count")
    private String commentCount;
}
