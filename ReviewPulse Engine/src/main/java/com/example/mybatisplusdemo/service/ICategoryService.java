package com.example.mybatisplusdemo.service;

import com.example.mybatisplusdemo.model.domain.Category;
import com.baomidou.mybatisplus.extension.service.IService;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.dto.MerchantCurrentDTO;

import java.util.List;


public interface ICategoryService extends IService<Category> {
    
    List<String> getAllSubCategoryIds(String categoryId);

    Integer insertMy(Category category);

    Integer deleteMy(String categoryId);

    Integer updateMy(Category category);

    List getParentList();

    Category getMerchantCategoryName(String category);
}
