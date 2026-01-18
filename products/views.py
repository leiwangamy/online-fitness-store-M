from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import OperationalError, ProgrammingError


def product_list(request):
    """
    Product list page with search, category filters, and pagination.
    Handles database errors gracefully - shows static content if database is not available
    Filters:
    - ?q=<search_query> - Search by name
    - ?category=<slug> - Filter by category slug, or 'digital', 'services'
    - ?page=<n> - Pagination
    """
    search_query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    
    categories = []
    products = []
    page_obj = None
    total_products = 0
    
    # Try to get data from database, but handle errors gracefully
    try:
        from .models import Product, Category
        
        categories = Category.objects.all()
        # Prefetch images for efficient loading
        products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")

        # Filter by search query
        if search_query:
            products = products.filter(name__icontains=search_query)

        # Filter by category or product type
        if selected_category:
            if selected_category.lower() == "digital":
                products = products.filter(is_digital=True)
            elif selected_category.lower() == "services":
                products = products.filter(is_service=True)
            else:
                products = products.filter(category__slug=selected_category)

        # Order by newest first
        products = products.order_by("-id")
        
        total_products = products.count()

        # Paginate results (6 products per page for 3x2 grid)
        paginator = Paginator(products, 6)
        page_obj = paginator.get_page(request.GET.get("page"))
        
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - show static content only
        # Create empty paginator for template compatibility
        from django.core.paginator import Paginator as PaginatorClass
        paginator = PaginatorClass([], 6)
        page_obj = paginator.get_page(1)
        categories = []
        total_products = 0
    except Exception:
        # Any other database error - show static content
        from django.core.paginator import Paginator as PaginatorClass
        paginator = PaginatorClass([], 6)
        page_obj = paginator.get_page(1)
        categories = []
        total_products = 0

    return render(request, "products/product_list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
        "total_products": total_products,
    })


def home(request):
    """
    Home page:
    - category filter: ?category=<slug>
    - search: ?q=<text>
    - pagination: ?page=<n>
    """
    selected_category = request.GET.get("category", "").strip()
    search_query = request.GET.get("q", "").strip()

    # Prefetch images for efficient loading
    products = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")

    if selected_category:
        products = products.filter(category__slug=selected_category)

    if search_query:
        products = products.filter(name__icontains=search_query)

    products = products.order_by("-id")

    paginator = Paginator(products, 5)  # change per-page number if you want
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.all()

    return render(request, "home/home.html", {
        "categories": categories,
        "selected_category": selected_category,
        "search_query": search_query,
        "page_obj": page_obj,
        "total_products": products.count(),
    })


def product_detail(request, pk):
    """
    Product detail page
    Handles database errors gracefully - shows 404 if database is not available
    """
    product = None
    
    try:
        from .models import Product
        
        product = get_object_or_404(
            Product.objects.select_related("category").prefetch_related("images", "videos", "audios"),
            pk=pk,
            is_active=True
        )
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - return 404
        from django.http import Http404
        raise Http404("Product not found - database not available")
    except Exception:
        # Any other database error - return 404
        from django.http import Http404
        raise Http404("Product not found")
    
    return render(request, "products/product_detail.html", {"product": product})
