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
@TableName("reply")
@ApiModel(value="Reply对象", description="评论回复表")
public class Reply implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "主键")
    @TableId("reply_id")
    private String replyId;

        @ApiModelProperty(value = "所属评论 ID")
    @TableField("comment_id")
    private String commentId;

        @ApiModelProperty(value = "回复人 ID")
    @TableField("user_id")
    private String userId;

        @ApiModelProperty(value = "商家回复 ID")
    @TableField("merchant_id")
    private String merchantId;

        @ApiModelProperty(value = "被回复人 ID（可为 null）")
    @TableField("reply_to")
    private String replyTo;

        @ApiModelProperty(value = "回复内容")
    @TableField("reply_content")
    private String replyContent;

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
