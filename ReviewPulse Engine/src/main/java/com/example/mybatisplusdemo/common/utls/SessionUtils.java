package com.example.mybatisplusdemo.common.utls;


import com.example.mybatisplusdemo.model.domain.Admin;
import com.example.mybatisplusdemo.model.domain.Merchant;
import com.example.mybatisplusdemo.model.domain.User;
import jakarta.servlet.http.HttpSession;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;



public class SessionUtils {
    private static final String USERKEY = "sessionUser";

    public static HttpSession session() {
        ServletRequestAttributes attr = (ServletRequestAttributes) RequestContextHolder.currentRequestAttributes();
        return attr.getRequest().getSession(true);
    }

    public static User getCurrentUserInfo() {
        return (User) session().getAttribute(USERKEY);
    }

    public static void saveCurrentUserInfo(User admin) {
        session().setAttribute(USERKEY, admin);
    }

    public static Merchant getCurrentMerchantInfo() {
        return (Merchant) session().getAttribute(USERKEY);
    }

    public static void saveCurrentMerchantInfo(Merchant admin) {
        session().setAttribute(USERKEY, admin);
    }

    public static Admin getCurrentAdminInfo() {
        return (Admin) session().getAttribute(USERKEY);
    }

    public static void saveCurrentAdminInfo(Admin admin) {
        session().setAttribute(USERKEY, admin);
    }
}
