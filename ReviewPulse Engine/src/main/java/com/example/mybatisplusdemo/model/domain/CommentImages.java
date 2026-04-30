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
@TableName("comment_images")
@ApiModel(value="CommentImages对象", description="")
public class CommentImages implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId("comment_images_id")
    private String commentImagesId;

    @TableField("comment_id")
    private String commentId;

    @TableField("url")
    private String url;

        @ApiModelProperty(value = "是否删除(T/F)")
    @TableField("is_deleted")
    private String isDeleted;

        @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

        @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;


}
