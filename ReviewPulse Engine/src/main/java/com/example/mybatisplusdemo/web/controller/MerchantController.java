package com.example.mybatisplusdemo.web.controller;

import com.example.mybatisplusdemo.common.utls.SessionUtils;
import com.example.mybatisplusdemo.mapper.MerchantMapper;
import com.example.mybatisplusdemo.model.domain.Category;
import com.example.mybatisplusdemo.model.domain.User;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Param;
import org.springframework.web.bind.annotation.RequestMapping;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.example.mybatisplusdemo.common.JsonResponse;
import com.example.mybatisplusdemo.service.IMerchantService;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.mybatisplusdemo.model.dto.MerchantSearchDTO;
import com.example.mybatisplusdemo.service.ICategoryService;

import java.util.List;



@RestController
@RequestMapping("/api/merchant")
public class MerchantController {

    private final Logger logger = LoggerFactory.getLogger( MerchantController.class );
    @Autowired
    private IMerchantService merchantService;

    @Autowired
    private ICategoryService categoryService;

    @Autowired
    private MerchantMapper merchantMapper;

    
    @RequestMapping(value = "/{id:\\d+}", method = RequestMethod.GET)
    @ResponseBody
    public JsonResponse<Merchant> getById(@PathVariable("id") Long id)throws Exception {
        Merchant merchant = merchantService.getById(id);
        return JsonResponse.success(merchantService.getById(merchant));
    }

    @GetMapping("selectById")
    public  JsonResponse<Merchant> selectMy(Long id)throws Exception {
        return JsonResponse.success(merchantService.getById(id));
    }

    @PostMapping("insert")
    public JsonResponse<Merchant> insertMy(@RequestBody Merchant merchant)throws Exception{
        merchantService.insertMy(merchant);
        return JsonResponse.success(merchantService.getById(merchant.getMerchantId()));
    }

    @DeleteMapping("delete")
    public JsonResponse<Merchant> deleteMy(Merchant merchant)throws Exception {
        merchantService.deleteMy(merchant.getMerchantId());
        return JsonResponse.success(merchantService.getById(merchant));
    }

    @PostMapping("/deleteById")
    public JsonResponse deleteById(@RequestParam String merchantId) {
        boolean b = merchantService.removeById(merchantId);
        if (b) {
            return JsonResponse.successMessage("商家删除成功");
        } else {
            return JsonResponse.failure("商家删除失败");
        }
    }

    @PostMapping("update")
    public JsonResponse<Merchant> updateMy(@RequestBody Merchant merchant)throws Exception{
        merchantService.updateMy(merchant);
        return JsonResponse.success(merchantService.getById(merchant));
    }

    @GetMapping("selectBySearch")
    public  JsonResponse<List<Merchant>> selectBySearch(String keyword)throws Exception {
        return JsonResponse.success(merchantService.selectBySearch(keyword));
    }

    @PostMapping("selectByDynamicSql")
    public JsonResponse<List<Merchant>> selectByDynamicSql(@RequestBody Merchant merchant) throws Exception {
        return JsonResponse.success(merchantService.selectByDynamicSql(merchant));
    }

    
    @PostMapping("/search")
    public JsonResponse<Page<Merchant>> search(@RequestBody MerchantSearchDTO dto) {
        java.util.List<String> categoryIds = null;
        if (dto.getCategoryId() != null) {
            categoryIds = categoryService.getAllSubCategoryIds(dto.getCategoryId());
        }
        Page<Merchant> page = merchantService.searchMerchants(dto, categoryIds);
        return JsonResponse.success(page);
    }

    @PostMapping("/login")
    public JsonResponse<Merchant> login(@RequestBody Merchant merchant) {
        return merchantService.login(merchant);
    }

    @GetMapping("/getInfo")
    public JsonResponse<Merchant> getInfo() {
        Merchant currentMerchant = SessionUtils.getCurrentMerchantInfo();
        if (currentMerchant != null) {
            return JsonResponse.success(currentMerchant);
        } else {
            return JsonResponse.failure("未登录或用户信息不存在");
        }
    }

    
    @PostMapping("/list")
    public JsonResponse<Page<Merchant>> listAll(
            @RequestParam(defaultValue = "1") int pageNum,
            @RequestParam(defaultValue = "10") int pageSize) {
        Page<Merchant> page = merchantService.listAllAsPage(pageNum, pageSize);
        return JsonResponse.success(page);
    }

    
    @GetMapping("/calDistance")
    public JsonResponse<Double> calcDistance(@RequestParam double lat1, @RequestParam double lng1, @RequestParam double lat2, @RequestParam double lng2) {
        double distance = this.calcDis(lat1, lng1, lat2, lng2);
        return JsonResponse.success(distance);
    }

    
    private double calcDis(double lat1, double lng1, double lat2, double lng2) {
        double R = 6371.0;
        double dLat = Math.toRadians(lat2 - lat1);
        double dLng = Math.toRadians(lng2 - lng1);
        double a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    
    @GetMapping("/getList")
    public JsonResponse<Page<Merchant>> getMerchantList(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String searchQuery) {

        Page<Merchant> page = new Page<>(pageNum, pageSize);
        return JsonResponse.success(merchantService.searchMerchantsLike(page, searchQuery));
    }

    @PostMapping("/verify")
    public JsonResponse<Merchant> verifyMerchant(
            @RequestParam String merchantId,
            @RequestParam Byte verificationStatus,
            @RequestParam(required = false) String review) {

        try {
            if (merchantId == null || merchantId.isEmpty()) {
                return JsonResponse.failure("商家ID不能为空");
            }
            if (verificationStatus == null || (verificationStatus != 0 && verificationStatus != 1 && verificationStatus != 2)) {
                return JsonResponse.failure("审核状态必须是0(不通过)、1(审核中)或2(通过)");
            }

            Merchant merchant = merchantService.getById(merchantId);
            if (merchant == null) {
                return JsonResponse.failure("商家不存在");
            }

            merchant.setVerificationStatus(verificationStatus);
            merchant.setReview(review);
            merchantService.updateMy(merchant);

            return JsonResponse.success(merchant);

        } catch (Exception e) {
            return JsonResponse.failure(e.getMessage());
        }
    }

    @PostMapping("/status")
    public JsonResponse<String> toggleMerchantStatus(
            @RequestParam String merchantId,
            @RequestParam String status) {

        try {
            if (merchantId == null) {
                return JsonResponse.failure("商家ID不能为空");
            }
            if (!"active".equals(status) && !"frozen".equals(status)) {
                return JsonResponse.failure("状态值必须是active或frozen");
            }

            Merchant merchant = merchantService.getById(merchantId);
            if (merchant == null) {
                return JsonResponse.failure("商家不存在");
            }

            merchant.setMerchantStatus(status);
            merchantService.updateMy(merchant);

            return JsonResponse.successMessage("操作成功");

        } catch (Exception e) {
            return JsonResponse.failure("操作失败: " + e.getMessage());
        }
    }

}
