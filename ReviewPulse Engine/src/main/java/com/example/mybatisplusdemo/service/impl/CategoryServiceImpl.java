package com.example.mybatisplusdemo.service.impl;

import com.example.mybatisplusdemo.model.domain.Category;
import com.example.mybatisplusdemo.mapper.CategoryMapper;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.dto.MerchantCurrentDTO;
import com.example.mybatisplusdemo.service.ICategoryService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;


@Service
public class CategoryServiceImpl extends ServiceImpl<CategoryMapper, Category> implements ICategoryService {

    @Override
    public List<String> getAllSubCategoryIds(String categoryId) {
        List<String> result = new ArrayList<>();
        result.add(categoryId);
        List<Category> all = this.list();
        addChildren(categoryId, all, result);
        return result;
    }

    private void addChildren(String parentId, List<Category> all, List<String> result) {
        for (Category c : all) {
            if (parentId.equals(c.getParentId())) {
                result.add(c.getCategoryId());
                addChildren(c.getCategoryId(), all, result);
            }
        }
    }
    @Autowired
    CategoryMapper categoryMapper;

    public Integer insertMy(Category category) {
        return categoryMapper.insertMy(category);
    }

    @Override
    public Integer deleteMy(String categoryId) {
        return categoryMapper.deleteMy(categoryId);
    }

    @Override
    public Integer updateMy(Category category) {
        return categoryMapper.updateMy(category);
    }

    @Override
    public List<Category> getParentList() {
        return categoryMapper.getParentList();
    }

    @Override
    public Category getMerchantCategoryName(String categoryId) {
        return categoryMapper.getCategoryName(categoryId);
    }
}
