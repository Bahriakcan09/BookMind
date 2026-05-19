using Firebase.Database;
using Firebase.Database.Query;
using HackatonProject.Models;
using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace HackatonProject.Services
{
    public class FirebaseService : IFirebaseService
    {
        private readonly FirebaseClient _dbClient;
        private readonly string _apiKey;

        public FirebaseService(IConfiguration configuration)
        {
            var dbUrl = configuration["Firebase:DatabaseUrl"] ?? "";
            _apiKey = configuration["Firebase:ApiKey"] ?? "";
            _dbClient = new FirebaseClient(dbUrl);
        }

        public async Task<string?> LoginAsync(string email, string password)
        {
            // Note: Proper Firebase Auth usually involves a separate REST call or Client-side SDK.
            // For this project, we'll assume authentication is successful if credentials are valid.
            // In a real scenario, we'd use Firebase Auth REST API to get a token.
            return Guid.NewGuid().ToString(); // Placeholder for UID
        }

        public async Task<bool> RegisterAsync(string email, string password)
        {
            return true;
        }

        public async Task<List<Product>> GetProductsAsync()
        {
            var products = await _dbClient
                .Child("products")
                .OnceAsync<Product>();

            return products.Select(item => {
                var p = item.Object;
                p.Id = item.Key;
                return p;
            }).ToList();
        }

        public async Task<Product?> GetProductByIdAsync(string id)
        {
            return await _dbClient
                .Child("products")
                .Child(id)
                .OnceSingleAsync<Product>();
        }

        public async Task SaveOrderAsync(Order order)
        {
            await _dbClient
                .Child("orders")
                .PostAsync(order);
        }

        public async Task<List<Order>> GetUserOrdersAsync(string userId)
        {
            var orders = await _dbClient
                .Child("orders")
                .OrderBy("UserId")
                .EqualTo(userId)
                .OnceAsync<Order>();

            return orders.Select(item => {
                var o = item.Object;
                o.Id = item.Key;
                return o;
            }).ToList();
        }

        public async Task<Product?> MatchProductByNameAsync(string ingredientName)
        {
            var products = await GetProductsAsync();
            // Simple match logic for now
            return products.FirstOrDefault(p => p.Name.Contains(ingredientName, StringComparison.OrdinalIgnoreCase));
        }
    }
}
