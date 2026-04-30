package com.example.mybatisplusdemo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.mapper.CategoryMapper;
import com.example.mybatisplusdemo.mapper.CommentMapper;
import com.example.mybatisplusdemo.mapper.UserMapper;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.mapper.MerchantMapper;
import com.example.mybatisplusdemo.service.IMerchantService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.mybatisplusdemo.model.dto.MerchantSearchDTO;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Map;


@Service
public class MerchantServiceImpl extends ServiceImpl<MerchantMapper, Merchant> implements IMerchantService {

    @Autowired
    private MerchantMapper merchantMapper;
    @Autowired
    private UserMapper userMapper;
    @Autowired
    private CategoryMapper categoryMapper;
    @Autowired
    private CommentMapper commentMapper;

    @Override
    public List<Merchant> selectBySearch(String keyword) {
        return merchantMapper.selectBySearch(keyword);
    }

    @Override
    public Integer insertMy(Merchant merchant) {

        return merchantMapper.insertMy(merchant);
    }

    @Override
    public Integer deleteMy(String merchantId) {
        return merchantMapper.deleteMy(merchantId);
    }

    @Override
    public Integer updateMy(Merchant merchant) {
        return merchantMapper.updateMy(merchant);
    }

    @Override
    public List<Merchant> selectByDynamicSql(Merchant merchant) {
        return merchantMapper.selectByDynamicSql(merchant);
    }

    @Override
    public JsonResponse login(Merchant merchant) {
        LambdaQueryWrapper<Merchant> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(Merchant::getMerchantName, merchant.getMerchantName())
                    .eq(Merchant::getMerchantPassword, merchant.getMerchantPassword());
        Merchant currentMerchant = merchantMapper.selectOne(queryWrapper);

        if (currentMerchant == null) {
            return JsonResponse.failure("用户不存在或密码错误");
        }

        if ("active".equals(currentMerchant.getMerchantStatus())) {
            SessionUtils.saveCurrentMerchantInfo(currentMerchant);
            return JsonResponse.success(currentMerchant, "登录成功");
        } else if ("frozen".equals(currentMerchant.getMerchantStatus())) {
            return JsonResponse.failure("用户被冻结");
        } else {
            return JsonResponse.failure("未知用户状态");
        }
    }

    @Override
    public Page<Merchant> searchMerchants(MerchantSearchDTO dto, List<String> categoryIds) {
        Page<Merchant> page = new Page<>(dto.getPageNum(), dto.getPageSize());
        QueryWrapper<Merchant> query = new QueryWrapper<>();
        if (categoryIds != null && !categoryIds.isEmpty()) {
            query.in("category_id", categoryIds);
        }
        if (dto.getMinScore() != null && !dto.getMinScore().isEmpty()) {
            query.ge("avg_rating", Double.parseDouble(dto.getMinScore()));
        }
        if (dto.getMaxScore() != null && !dto.getMaxScore().isEmpty()) {
            query.le("avg_rating", Double.parseDouble(dto.getMaxScore()));
        }
        if (dto.getMinPrice() != null && !dto.getMinPrice().isEmpty()) {
            query.ge("price_level", Double.parseDouble(dto.getMinPrice()));
        }
        if (dto.getMaxPrice() != null && !dto.getMaxPrice().isEmpty()) {
            query.le("price_level", Double.parseDouble(dto.getMaxPrice()));
        }
        if (StringUtils.hasText(dto.getMerchantName())) {
            query.like("merchant_name", dto.getMerchantName());
        }
        if (StringUtils.hasText(dto.getSortBy())) {
            switch (dto.getSortBy()) {
                case "score":
                    query.orderByDesc("avg_rating");
                    break;
                case "price":
                    query.orderByAsc("price_level");
                    break;
            }
        }
        Page<Merchant> result = this.page(page, query);
        if ("distance".equals(dto.getSortBy()) && dto.getUserLat() != null && !dto.getUserLat().isEmpty() && dto.getUserLng() != null && !dto.getUserLng().isEmpty()) {
            double userLat = Double.parseDouble(dto.getUserLat());
            double userLng = Double.parseDouble(dto.getUserLng());
            result.getRecords().sort((a, b) -> {
                Double da = (a.getLatitude() != null && a.getLongitude() != null) ? calcDistance(userLat, userLng, a.getLatitude(), a.getLongitude()) : Double.MAX_VALUE;
                Double db = (b.getLatitude() != null && b.getLongitude() != null) ? calcDistance(userLat, userLng, b.getLatitude(), b.getLongitude()) : Double.MAX_VALUE;
                return da.compareTo(db);
            });
        }
        return result;
    }

    
    @Override
    public Page<Merchant> listAllAsPage(int pageNum, int pageSize) {
        Page<Merchant> page = new Page<>(pageNum, pageSize);
        return this.page(page);
    }

    @Override
    public Page<Merchant> searchMerchantsLike(Page<Merchant> page, String query) {
        if (com.baomidou.mybatisplus.core.toolkit.StringUtils.isBlank(query)) {
            return this.page(page);
        }

        return lambdaQuery()
                .and(wrapper -> wrapper
                        .like(Merchant::getMerchantName, query)
                        .or()
                        .like(Merchant::getContactPhone, query)
                        .or()
                        .like(Merchant::getContactEmail, query)
                )
                .page(page);
    }



    
    public double calcDistance(double lat1, double lng1, double lat2, double lng2) {
        double R = 6371.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLng = Math.toRadians(lng2 - lng1);
        double a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    @Override
    public List<Map<String, Object>> getFiveStarMerchants() {
        return baseMapper.selectFiveStarMerchants();
    }

    @Override
    public List<Map<String, Object>> getMostCommentedMerchants() {
        return baseMapper.selectMostCommentedMerchants();
    }

    @Override
    public List<Map<String, Object>> getHighestRatedMerchants() {
        return baseMapper.selectHighestRatedMerchants();
    }

    @Override
    public List<Map<String, Object>> getRatingDistribution() {
        return baseMapper.selectRatingDistribution();
    }

}
