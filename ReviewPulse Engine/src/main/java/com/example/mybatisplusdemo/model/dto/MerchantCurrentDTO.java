package com.example.mybatisplusdemo.model.dto;

import com.example.mybatisplusdemo.model.domain.Merchant;
import lombok.Data;

@Data
public class MerchantCurrentDTO extends Merchant {

    private String categoryName;
}
