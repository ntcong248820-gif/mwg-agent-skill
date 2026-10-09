import sys, pathlib, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from kw_rules import classify


def v(kw, ctx):
    return classify(kw, ctx)[0]


class SanPham(unittest.TestCase):
    ctx = {"type": "sp", "name": "Laptop Lenovo V14 G5 IRL R5 7520U/16GB/512GB (83HD0035VN)",
           "url": "lenovo-v14-g5-irl-83hd0035vn"}

    def test_dinh_danh_bang_ma(self):
        self.assertEqual(v("83hd0035vn", self.ctx), "keep")

    def test_hang_va_dong(self):
        self.assertEqual(v("laptop lenovo v14 g5 irl 83hd0035vn", self.ctx), "keep")
        self.assertEqual(v("lenovo v14 g5", self.ctx), "keep")

    def test_sai_ma_bien_the(self):  # mã SKU của biến thể khác
        self.assertEqual(v("laptop lenovo v14 g5 irl 83hd0062va", self.ctx), "drop")

    def test_blog_va_chung_chung(self):
        self.assertEqual(v("review lenovo v14 g5", self.ctx), "drop")
        self.assertNotEqual(v("laptop văn phòng", self.ctx), "keep")

    def test_ten_ngan_khong_hang(self):
        ctx = {"type": "sp", "name": "Samsung Galaxy Z Fold8 Ultra 5G", "url": "samsung-galaxy-z-fold8-ultra"}
        self.assertEqual(v("z fold 8", ctx), "keep")


class Filter(unittest.TestCase):
    oled = {"type": "nh", "nganh": "màn hình máy tính", "filter": "OLED", "url": "man-hinh-may-tinh-oled"}

    def test_thuoc_tinh_filter_khong_bi_loai(self):  # filter oled thì chữ oled phải giữ
        self.assertEqual(v("màn hình oled", self.oled), "keep")
        self.assertEqual(v("màn hình máy tính oled giá rẻ", self.oled), "keep")
        ctx = {"type": "nh", "nganh": "laptop", "filter": "15.6 inch", "url": "laptop-15-6-inch"}
        self.assertEqual(v("laptop 15.6 inch", ctx), "keep")
        ctx = {"type": "nh", "nganh": "thẻ nhớ", "filter": "16 GB", "url": "the-nho-16gb"}
        self.assertEqual(v("thẻ nhớ 16gb", ctx), "keep")

    def test_thong_so_khac_filter(self):
        self.assertEqual(v("màn hình ips 27 inch", self.oled), "review")

    def test_intent_va_sku(self):
        self.assertEqual(v("review màn hình oled", self.oled), "drop")
        self.assertEqual(v("màn hình oled m6702dw", self.oled), "drop")

    def test_dong_filter_giu_ten_dong_va_nam(self):
        ctx = {"type": "dong", "nganh": "laptop", "filter": "tuf gaming f15", "url": "laptop-asus-tuf-gaming-f15"}
        self.assertEqual(v("asus tuf gaming f15 2023", ctx), "keep")
        self.assertEqual(v("laptop asus tuf gaming f15", ctx), "keep")


class FilterCaseMoi(unittest.TestCase):
    ctx = {"type": "nh", "nganh": "màn hình máy tính", "filter": "8K", "url": "man-hinh-may-tinh-8k"}
    ryzen = {"type": "nh", "nganh": "laptop", "filter": "Ryzen 3", "url": "laptop-ryzen-3"}

    def test_y_dinh_tim_anh(self):
        self.assertEqual(v("ảnh màn hình máy tính 8k", self.ctx), "drop")
        self.assertEqual(v("hình ảnh màn hình 8k", self.ctx), "drop")
        cam = {"type": "nh", "nganh": "máy ảnh", "filter": "chụp ảnh", "url": "may-anh-chup-anh"}
        self.assertEqual(v("máy chụp ảnh cầm tay", cam), "keep")   # "ảnh" trong ngữ cảnh máy ảnh vẫn giữ
        ip = {"type": "hang", "nganh": "máy in", "hang": "Xiaomi", "url": "may-in-xiaomi"}
        self.assertEqual(v("máy in ảnh xiaomi", ip), "keep")        # máy in ảnh là sản phẩm

    def test_cung_ho_khac_so(self):
        self.assertEqual(v("laptop ryzen 5", self.ryzen), "drop")
        self.assertEqual(v("laptop ryzen 3", self.ryzen), "keep")

    def test_dang_chua_tung_duyet(self):
        gc = {"type": "nh", "nganh": "máy chơi game cầm tay", "filter": "máy chơi game", "url": "may-choi-game-cam-tay"}
        for kw in ("máy chơi game cầm tay cũ", "máy chơi game cầm tay đà nẵng", "top máy chơi game cầm tay"):
            self.assertEqual(v(kw, gc), "review", kw)
        self.assertEqual(v("máy chơi game cầm tay giá rẻ", gc), "keep")


class RuleTuKhoa(unittest.TestCase):
    CTX = {"type": "nh", "nganh": "màn hình máy tính", "filter": "5K"}

    def test_thieu_dau_bi_loai(self):
        self.assertEqual(classify("man hinh 5k", self.CTX)[0], "drop")
        self.assertEqual(classify("màn hình 5k", self.CTX)[0], "keep")

    def test_tu_khong_dau_hop_le_van_giu(self):
        self.assertEqual(classify("laptop 300hz", {"type": "nh", "nganh": "laptop", "filter": "300 hz"})[0], "keep")

    def test_nha_ban_le_bi_loai(self):
        self.assertEqual(classify("màn hình 5k thế giới di động", self.CTX)[0], "drop")
        self.assertEqual(classify("màn hình 5k fpt shop", self.CTX)[0], "drop")


class FilterBonNhomLoi(unittest.TestCase):
    """Bốn nhóm keyword không hợp URL filter: trỏ riêng hãng/dòng, blog/danh sách, phân khúc chi tiết hơn, tiếng Anh."""
    CTX = {
        "300": {"type": "nh", "nganh": "laptop", "filter": "300 hz"},
        "ryzen": {"type": "nh", "nganh": "laptop", "filter": "amd ryzen 3"},
        "5k": {"type": "nh", "nganh": "màn hình máy tính", "filter": "5K"},
        "8k": {"type": "nh", "nganh": "màn hình máy tính", "filter": "8K"},
        "game": {"type": "nh", "nganh": "máy chơi game cầm tay", "filter": "Máy chơi game"},
    }
    BAD = {
        "300": ["300hz refresh rate laptop", "laptop 300hz screen", "rog 300hz laptop", "omen laptop 300hz",
                "omen 300hz laptop", "300hz laptop screen"],
        "ryzen": ["ryzen 3 5000 series laptop", "ryzen 3 6000 series laptop"],
        "5k": ["màn hình kuycon 5k"],
        "8k": ["độ phân giải màn hình 8k", "laptop màn hình 8k", "video 8k test màn hình"],
        "game": ["máy chơi game cầm tay android", "máy chơi game cầm tay switch", "máy chơi game cầm tay nintendo switch",
                 "máy chơi game cầm tay ps5", "các loại máy chơi game cầm tay", "máy chơi game cầm tay giá rẻ 100k",
                 "máy chơi game cầm tay steam deck", "các máy chơi game cầm tay", "máy chơi game cầm tay giá rẻ 50k"],
    }

    def test_keyword_sai_bi_loai(self):
        for k, kws in self.BAD.items():
            for kw in kws:
                self.assertNotEqual(classify(kw, self.CTX[k])[0], "keep", kw)

    def test_keyword_dung_van_giu(self):
        for k, kw in [("300", "laptop 300hz"), ("ryzen", "laptop ryzen 3"), ("5k", "màn hình 5k"),
                      ("8k", "màn hình máy tính 8k"), ("game", "máy chơi game cầm tay"),
                      ("game", "máy chơi game cầm tay giá rẻ"), ("5k", "màn hình chơi game 5k")]:
            self.assertEqual(classify(kw, self.CTX[k])[0], "keep", kw)

    def test_filter_gia_van_nhan_khoang_gia(self):
        ctx = {"type": "nh", "nganh": "điện thoại", "filter": "dưới 2 triệu"}
        self.assertEqual(classify("điện thoại dưới 2 triệu", ctx)[0], "keep")


class Hang(unittest.TestCase):
    ctx = {"type": "hang", "nganh": "máy in", "hang": "Pantum", "url": "may-in-pantum"}

    def test_hop_le(self):
        for kw in ("máy in pantum", "máy in pantum giá rẻ", "mua máy in pantum"):
            self.assertEqual(v(kw, self.ctx), "keep", kw)

    def test_loai(self):
        self.assertEqual(v("driver máy in pantum", self.ctx), "drop")
        self.assertEqual(v("máy in pantum p2200", self.ctx), "drop")
        self.assertEqual(v("máy in pantum 2025", self.ctx), "drop")
        self.assertEqual(v("máy in canon", self.ctx), "drop")


class IntentBlogLot(unittest.TestCase):
    """Keyword intent blog không được lọt, intent mua không bị loại oan. Mẫu nằm ở known_intent_keywords.json."""
    import json as _json, os as _os
    data = _json.load(open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                         "known_intent_keywords.json"), encoding="utf-8"))
    ctxs = [("laptop asus", {"type": "hang", "nganh": "laptop", "hang": "Asus", "name": "Laptop Asus", "url": "laptop-asus"}),
            ("laptop gaming", {"type": "nh", "nganh": "laptop", "filter": "gaming", "url": "laptop-gaming"})]

    def test_blog_khong_duoc_keep(self):
        for x, ctx in self.ctxs:
            for t in self.data["blog"]:
                self.assertNotEqual(v(t.format(x=x), ctx), "keep", t.format(x=x))

    def test_intent_mua_van_keep(self):
        for x, ctx in self.ctxs:
            for t in self.data["buy"]:
                self.assertEqual(v(t.format(x=x), ctx), "keep", t.format(x=x))

    def test_cach_am_khong_bi_loai(self):  # "cách" là intent blog, nhưng "cách âm" là thuộc tính loa/tai nghe
        ctx = {"type": "nh", "nganh": "tai nghe", "filter": "chống ồn", "url": "tai-nghe-chong-on"}
        self.assertNotEqual(v("tai nghe chống ồn cách âm", ctx), "drop")
        self.assertEqual(v("cách chọn tai nghe chống ồn", ctx), "drop")

    def test_tu_mo_ho_la_review_khong_phai_drop(self):
        ctx = self.ctxs[0][1]
        for kw in ("laptop asus tốt", "top laptop asus", "laptop asus mới nhất"):
            self.assertEqual(v(kw, ctx), "review", kw)


if __name__ == "__main__":
    unittest.main(verbosity=1)
