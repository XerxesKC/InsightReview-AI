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
@TableName("merchant")
@ApiModel(value="Merchant对象", description="商家信息表")
public class Merchant implements Serializable {

    private static final long serialVersionUID = 1L;

        @ApiModelProperty(value = "商家主键")
    @TableId("merchant_id")
    private String merchantId;

        @ApiModelProperty(value = "商家名称")
    @TableField("merchant_name")
    private String merchantName;

        @ApiModelProperty(value = "商家密码")
    @TableField("merchant_password")
    private String merchantPassword;

        @ApiModelProperty(value = "商家描述")
    @TableField("description")
    private String description;

        @ApiModelProperty(value = "所属子类别 ID")
    @TableField("category_id")
    private String categoryId;

        @ApiModelProperty(value = "标签")
    @TableField("tag")
    private String tag;

        @ApiModelProperty(value = "联系电话")
    @TableField("contact_phone")
    private String contactPhone;

        @ApiModelProperty(value = "联系邮箱")
    @TableField("contact_email")
    private String contactEmail;

        @ApiModelProperty(value = "地址")
    @TableField("address")
    private String address;

        @ApiModelProperty(value = "封面图片")
    @TableField("cover_image")
    private String coverImage;

        @ApiModelProperty(value = "营业执照")
    @TableField("business_license")
    private String businessLicense;

        @ApiModelProperty(value = "卫生许可证")
    @TableField("hygienic_license")
    private String hygienicLicense;

        @ApiModelProperty(value = "认证状态")
    @TableField("verification_status")
    private Byte verificationStatus;

        @ApiModelProperty(value = "营业时间")
    @TableField("business_hours")
    private String businessHours;

        @ApiModelProperty(value = "平均评分（1~5）")
    @TableField("avg_rating")
    private String avgRating;

        @ApiModelProperty(value = "人均消费")
    @TableField("price_level")
    private String priceLevel;

        @ApiModelProperty(value = "账号状态")
    @TableField("merchant_status")
    private String merchantStatus;

        @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

        @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;

        @ApiModelProperty(value = "是否删除")
    @TableField("is_deleted")
    private String isDeleted;

        @ApiModelProperty(value = "经度")
    @TableField("longitude")
    private Double longitude;

    @ApiModelProperty(value = "纬度")
    @TableField("latitude")
    private Double latitude;

        @ApiModelProperty(value = "审核信息")
    @TableField("review")
    private String review;

}
