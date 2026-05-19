using HackatonProject.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace HackatonProject.Services
{
    public interface IFirebaseService
    {
        // Auth (Simplified for this project, usually handled via client-side or specific SDK calls)
        Task<string?> LoginAsync(string email, string password);
        Task<bool> RegisterAsync(string email, string password);

        // Database
        Task<List<Product>> GetProductsAsync();
        Task<Product?> GetProductByIdAsync(string id);
        Task SaveOrderAsync(Order order);
        Task<List<Order>> GetUserOrdersAsync(string userId);
        
        // Product Matching
        Task<Product?> MatchProductByNameAsync(string ingredientName);
    }
}
