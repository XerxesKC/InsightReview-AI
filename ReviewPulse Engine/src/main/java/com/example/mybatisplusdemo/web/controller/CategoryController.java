package com.example.mybatisplusdemo.web.controller;

import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.dto.MerchantCurrentDTO;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.ICategoryService;
import com.example.mybatisplusdemo.model.domain.Category;



@RestController
@RequestMapping("/api/category")
public class CategoryController {

    private final Logger logger = LoggerFactory.getLogger( CategoryController.class );

    @Autowired
    private ICategoryService categoryService;


    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<Category> getById(@PathVariable("id") Long id)throws Exception {
        Category category = categoryService.getById(id);
        return JsonResponse.success(category);
    }

    @GetMapping("selectById")
    public  JsonResponse<Category> selectById(Long id)throws Exception {
        Category category = categoryService.getById(id);
        return JsonResponse.success(category);
    }

    @PostMapping("insert")
    public JsonResponse<Category> insert(@RequestBody Category category)throws Exception{
        long count = categoryService.count() + 1;
        category.setCategoryId(count + "");
        categoryService.insertMy(category);
        return JsonResponse.success(categoryService.getById(category.getCategoryId()));
    }

    @DeleteMapping("delete")
    public JsonResponse<Category> deleteMy(Category category) throws Exception {
        categoryService.deleteMy(category.getCategoryId());
        return JsonResponse.success(categoryService.getById(category));
    }

    @PostMapping("update")
    public JsonResponse<Category> updateMy(@RequestBody Category category)throws Exception{
        categoryService.updateMy(category);
        return JsonResponse.success(categoryService.getById(category));
    }

    
    @GetMapping("/list")
    public JsonResponse<java.util.List<Category>> listAll() {
        java.util.List<Category> list = categoryService.list();
        return JsonResponse.success(list);
    }

    
    @GetMapping("/getIdByName")
    public JsonResponse<String> getIdByName(@RequestParam String categoryName) {
        Category category = categoryService.lambdaQuery()
                .eq(Category::getCategoryName, categoryName)
                .one();
        if (category != null) {
            return JsonResponse.success(category.getCategoryId());
        } else {
            return JsonResponse.failure("未找到对应类别");
        }
    }

    @GetMapping("/getParentList")
    public  JsonResponse getParentList()throws Exception {
        return JsonResponse.success(categoryService.getParentList());
    }

    @GetMapping("/getMerchantCategoryName")
    public JsonResponse getMerchantCategoryName(@RequestParam String categoryId) throws Exception {
        Category category = categoryService.getMerchantCategoryName(categoryId);
        if (category != null) {
            return JsonResponse.success(category.getCategoryName());
        } else {
            return JsonResponse.failure("未找到对应商家类别");
        }
    }
}
