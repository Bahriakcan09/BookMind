using HackatonProject.Models;
using HackatonProject.Services;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HackatonProject.Controllers
{
    public class MarketController : Controller
    {
        private readonly IFirebaseService _firebaseService;

        public MarketController(IFirebaseService firebaseService)
        {
            _firebaseService = firebaseService;
        }

        public async Task<IActionResult> Index()
        {
            var products = await _firebaseService.GetProductsAsync();
            return View(products);
        }

        [HttpPost]
        public async Task<IActionResult> AddToCart(string productId, int quantity = 1)
        {
            var product = await _firebaseService.GetProductByIdAsync(productId);
            if (product != null)
            {
                var cart = GetCart();
                var item = cart.Items.FirstOrDefault(i => i.ProductId == productId);
                if (item != null)
                {
                    item.Quantity += quantity;
                }
                else
                {
                    cart.Items.Add(new CartItem
                    {
                        ProductId = productId,
                        ProductName = product.Name,
                        Price = product.Price,
                        Quantity = quantity,
                        ImageUrl = product.ImageUrl
                    });
                }
                SaveCart(cart);
            }
            return RedirectToAction("Cart");
        }

        public IActionResult Cart()
        {
            return View(GetCart());
        }

        [HttpPost]
        public IActionResult RemoveFromCart(string productId)
        {
            var cart = GetCart();
            var item = cart.Items.FirstOrDefault(i => i.ProductId == productId);
            if (item != null)
            {
                cart.Items.Remove(item);
                SaveCart(cart);
            }
            return RedirectToAction("Cart");
        }

        private Cart GetCart()
        {
            var session = HttpContext.Session.GetString("Cart");
            if (session == null) return new Cart { UserId = User.Identity?.Name ?? "Guest" };
            return JsonSerializer.Deserialize<Cart>(session) ?? new Cart();
        }

        private void SaveCart(Cart cart)
        {
            HttpContext.Session.SetString("Cart", JsonSerializer.Serialize(cart));
        }
    }
}
