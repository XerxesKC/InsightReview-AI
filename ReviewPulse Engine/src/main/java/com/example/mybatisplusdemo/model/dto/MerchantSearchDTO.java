package com.example.mybatisplusdemo.model.dto;

import lombok.Data;

@Data
public class MerchantSearchDTO {
    private String categoryId;
    private String minScore;
    private String maxScore;
    private String minPrice;
    private String maxPrice;
    private String userLng;
    private String userLat;
    private String sortBy;
    private Integer pageNum = 1;
    private Integer pageSize = 10;
    private String merchantName;
}
