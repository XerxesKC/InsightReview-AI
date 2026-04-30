package com.example.mybatisplusdemo.service;

import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.baomidou.mybatisplus.extension.service.IService;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.dto.MerchantSearchDTO;

import java.util.List;
import java.util.Map;


public interface IMerchantService extends IService<Merchant> {
    
    Page<Merchant> searchMerchants(MerchantSearchDTO dto, List<String> categoryIds);

    List<Merchant> selectBySearch(String keyword);

    Integer insertMy(Merchant merchant);

    Integer deleteMy(String merchantId);

    Integer updateMy(Merchant merchant);

    List<Merchant> selectByDynamicSql(Merchant merchant);

    JsonResponse login(Merchant merchant);

    
    Page<Merchant> listAllAsPage(int pageNum, int pageSize);

    Page<Merchant> searchMerchantsLike(Page<Merchant> page, String query);

    List<Map<String, Object>> getFiveStarMerchants();
    List<Map<String, Object>> getMostCommentedMerchants();
    List<Map<String, Object>> getHighestRatedMerchants();
    List<Map<String, Object>> getRatingDistribution();

}
