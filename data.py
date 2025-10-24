# Dữ liệu giả lập (mock data)
mockProducts = [
    {
      "id": 1,
      "name": "Tai Nghe Bluetooth Chụp Tai Baseus Bowie D05",
      "price": 459000,
      "image":
        "https://salt.tikicdn.com/cache/750x750/ts/product/05/e9/82/876c6b3e32ab945c7199c93399b1e9df.png",
      "vendor": "tiki",
      "link": "#",
      "bestDeal": True,
    },
    {
      "id": 2,
      "name": "Tai Nghe Không Dây Baseus Bowie D05 Chống Ồn",
      "price": 475000,
      "image":
        "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-log79q0lr8qb1a",
      "vendor": "shopee",
      "link": "#",
    },
    {
      "id": 3,
      "name": "Tai nghe chụp tai Baseus Bowie D05, Bluetooth 5.3",
      "price": 510000,
      "image":
        "https://lzd-img-global.slatic.net/g/p/mdc/d957d5402a559d7b92e212453e19865c.jpg_720x720q80.jpg",
      "vendor": "lazada",
      "link": "#",
    },
    {
      "id": 4,
      "name": "iPhone 15 Pro Max 256GB Chính hãng VN/A",
      "price": 29590000,
      "image":
        "https://salt.tikicdn.com/cache/750x750/ts/product/78/55/93/2f62a4ebf562fd1258160b943d0e2c8e.png",
      "vendor": "tiki",
      "link": "#",
      "bestDeal": True,
    },
    {
      "id": 5,
      "name": "Điện thoại Apple iPhone 15 Pro Max 256GB",
      "price": 29890000,
      "image":
        "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lq4z5tjq3a6g8b",
      "vendor": "shopee",
      "link": "#",
    },
    {
      "id": 6,
      "name": "Apple iPhone 15 Pro Max",
      "price": 30100000,
      "image":
        "https://lzd-img-global.slatic.net/g/p/ddedc5f11a843516317b6a67a054593f.jpg_720x720q80.jpg",
      "vendor": "lazada",
      "link": "#",
    },
]

vendorLogos = {
    "tiki": "https://salt.tikicdn.com/ts/upload/e4/49/6c/270be9859abd5f5ec5071da65fab0a94.png",
    "shopee": "https://deo.shopeemobile.com/shopee/shopee-pcmall-live-sg/assets/6c502a2641457578b0d5f5153b53dd5d.png",
    "lazada": "https://lzd-img-global.slatic.net/g/tps/tfs/TB1eIwcVhnaK1RjSZFBXXcW7VXa-72-72.png",
}

# Hàm tìm kiếm (logic tương tự trong script.js)
def search_products(query):
    query = query.lower().strip()
    if not query:
        return []
    
    filtered_products = [
        p for p in mockProducts if query in p["name"].lower()
    ]
    return filtered_products