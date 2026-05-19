using HackatonProject.Models;
using HackatonProject.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Security.Claims;
using System.Text.Json;
using System.Threading.Tasks;

namespace HackatonProject.Controllers
{
    [Authorize]
    public class OrderController : Controller
    {
        private readonly IFirebaseService _firebaseService;

        public OrderController(IFirebaseService firebaseService)
        {
            _firebaseService = firebaseService;
        }

        [HttpGet]
        public IActionResult Checkout()
        {
            var cart = GetCart();
            if (cart.Items.Count == 0) return RedirectToAction("Index", "Market");
            return View(cart);
        }

        [HttpPost]
        public async Task<IActionResult> PlaceOrder(string address)
        {
            var cart = GetCart();
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);

            if (userId != null && cart.Items.Count > 0)
            {
                var order = new Order
                {
                    UserId = userId,
                    Items = cart.Items,
                    TotalAmount = cart.TotalPrice,
                    Address = address,
                    OrderDate = DateTime.Now,
                    Status = "Preparing"
                };

                await _firebaseService.SaveOrderAsync(order);
                HttpContext.Session.Remove("Cart");
                return RedirectToAction("Track");
            }

            return RedirectToAction("Cart", "Market");
        }

        public async Task<IActionResult> Track()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            if (userId == null) return RedirectToAction("Login", "Account");

            var orders = await _firebaseService.GetUserOrdersAsync(userId);
            return View(orders);
        }

        private Cart GetCart()
        {
            var session = HttpContext.Session.GetString("Cart");
            if (session == null) return new Cart();
            return JsonSerializer.Deserialize<Cart>(session) ?? new Cart();
        }
    }
}
