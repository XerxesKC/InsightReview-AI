package com.example.mybatisplusdemo.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.mybatisplusdemo.model.domain.Merchant;
import org.apache.ibatis.annotations.MapKey;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;


public interface MerchantMapper extends BaseMapper<Merchant> {

    List<Merchant> selectBySearch(@Param("keyword") String keyword);

    Integer insertMy(@Param("merchant") Merchant merchant);

    Integer deleteMy(@Param("merchantId") String merchantId);

    Integer updateMy(@Param("merchant")  Merchant merchant);

    List<Merchant> selectByDynamicSql(Merchant merchant);

    @MapKey("five_star")
    List<Map<String, Object>> selectFiveStarMerchants();

    @MapKey("most_commented")
    List<Map<String, Object>> selectMostCommentedMerchants();

    @MapKey("highest_rated")
    List<Map<String, Object>> selectHighestRatedMerchants();

    @MapKey("rating_range")
    List<Map<String, Object>> selectRatingDistribution();
}
