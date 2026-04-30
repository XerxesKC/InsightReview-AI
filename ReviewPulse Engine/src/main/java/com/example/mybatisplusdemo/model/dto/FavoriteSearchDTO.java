package com.example.mybatisplusdemo.model.dto;

import lombok.Data;

@Data
public class FavoriteSearchDTO {
    private String userId;
    private String merchantId;
    private String merchantName;
    private String tag;
}

