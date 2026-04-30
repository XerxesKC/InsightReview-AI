package com.example.mybatisplusdemo.web.controller;

import com.example.mybatisplusdemo.service.IUserService;
import com.example.mybatisplusdemo.service.impl.UserServiceImpl;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.IFavoriteService;
import com.example.mybatisplusdemo.model.domain.Favorite;
import com.example.mybatisplusdemo.model.dto.FavoriteInsertDTO;
import com.example.mybatisplusdemo.model.dto.FavoriteUpdateDTO;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.dto.FavoriteDTO;
import com.example.mybatisplusdemo.model.vo.FavoriteSearchVO;
import com.example.mybatisplusdemo.model.dto.FavoriteSearchDTO;
import org.springframework.beans.BeanUtils;



@RestController
@RequestMapping("/api/favorite")
public class FavoriteController {

    private final Logger logger = LoggerFactory.getLogger( FavoriteController.class );

    @Autowired
    private IFavoriteService favoriteService;


    
    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<Favorite> getById(@PathVariable("id") Long id)throws Exception {
        Favorite favorite = favoriteService.getById(id);
        return JsonResponse.success(favorite);
    }

    
    @GetMapping("/search")
    public JsonResponse<Page<FavoriteSearchVO>> listFavorites(@RequestParam(defaultValue = "1") Integer pageNum,
                                                     @RequestParam(defaultValue = "10") Integer pageSize,
                                                     FavoriteSearchDTO favoriteSearchDTO) {
        Page<FavoriteSearchVO> page = new Page<>(pageNum, pageSize);
        page = favoriteService.searchFavorite(page, favoriteSearchDTO);
        return JsonResponse.success(page);
    }

    
    @PostMapping("/insert")
    public JsonResponse insertFavorite(@RequestBody FavoriteInsertDTO favoriteInsertDTO) {
        Favorite favorite = favoriteService.insertFavorite(favoriteInsertDTO);
        if (favorite != null) {
            return JsonResponse.success(favorite);
        } else {
            return JsonResponse.failure("新增收藏失败");
        }
    }

    
    @PostMapping("/delete")
    public JsonResponse deleteFavorite(@RequestParam String favoriteId) {
        Favorite favorite = favoriteService.deleteFavorite(favoriteId);
        if (favorite != null) {
            return JsonResponse.success(favorite);
        } else {
            return JsonResponse.failure("删除收藏失败");
        }
    }

    
    @PostMapping("/update")
    public JsonResponse updateFavorite(@RequestBody FavoriteUpdateDTO favoriteUpdateDTO) {
        Favorite favorite = favoriteService.updateFavorite(favoriteUpdateDTO);

        if (favorite != null) {
            return JsonResponse.success(favorite);
        } else {
            return JsonResponse.failure("更新失败");
        }
    }
}
