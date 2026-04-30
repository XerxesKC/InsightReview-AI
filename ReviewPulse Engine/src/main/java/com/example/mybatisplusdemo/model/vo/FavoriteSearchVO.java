package com.example.mybatisplusdemo.model.vo;

import lombok.Data;

@Data
public class FavoriteSearchVO {
    private String favoriteId;
    private String userId;
    private String merchantId;
    private String merchantName;
    private String description;
    private String address;
    private String tag;
    private String businessHours;
    private String avgRating;
    private String priceLevel;
    private String contactPhone;

}
