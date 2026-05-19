using Google.GenAI;
using Google.GenAI.Types;
using HackatonProject.Models;
using Microsoft.Extensions.Configuration;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HackatonProject.Services
{
    public class GeminiService : IGeminiService
    {
        private readonly Client _client;
        private readonly string _modelName = "gemini-2.5-flash";

        public GeminiService(IConfiguration configuration)
        {
            var apiKey = configuration["Gemini:ApiKey"] ?? "";
            _client = new Client(apiKey: apiKey);
        }

        public async Task<RecipeAnalysisResult?> AnalyzeImageAsync(byte[] imageBytes)
        {
            var prompt = """
                Bu yemek fotoğrafını analiz et. Yemeğin adını, tahmini hazırlık süresini ve gerekli malzemeleri (miktar ve birim ile birlikte) JSON formatında döndür. 
                JSON formatı şöyle olmalı: 
                { 
                    "RecipeName": "...", 
                    "PrepTime": "...", 
                    "Ingredients": [ { "Name": "...", "Amount": 0.0, "Unit": "..." } ] 
                }
                """;
            
            try 
            {
                var response = await _client.Models.GenerateContentAsync(
                    _modelName,
                    new List<Content> {
                        new Content {
                            Parts = new List<Part> {
                                new Part { Text = prompt },
                                new Part { InlineData = new Blob { MimeType = "image/jpeg", Data = imageBytes } }
                            }
                        }
                    }
                );

                var jsonResponse = response.Candidates[0].Content.Parts[0].Text;
                Console.WriteLine($"Gemini Response: {jsonResponse}"); // Debug için log
                return ParseJsonResponse(jsonResponse);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Gemini Image Error: {ex.Message}");
                if (ex.InnerException != null) Console.WriteLine($"Inner: {ex.InnerException.Message}");
                return null;
            }
        }

        public async Task<RecipeAnalysisResult?> AnalyzeLinkAsync(string url)
        {
            var prompt = $$"""
                Şu yemek tarifi linkini analiz et: {{url}}. Eğer link bir video ise içeriği tahmin etmeye çalış veya link başlığından yola çık. 
                Yemeğin adını, hazırlık süresini ve malzemeleri şu JSON formatında döndür: 
                { 
                    "RecipeName": "...", 
                    "PrepTime": "...", 
                    "Ingredients": [ { "Name": "...", "Amount": 0.0, "Unit": "..." } ] 
                }
                """;

            try
            {
                var response = await _client.Models.GenerateContentAsync(_modelName, prompt);
                var jsonResponse = response.Candidates[0].Content.Parts[0].Text;
                Console.WriteLine($"Gemini Response: {jsonResponse}"); // Debug için log
                return ParseJsonResponse(jsonResponse);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Gemini Link Error: {ex.Message}");
                return null;
            }
        }

        public async Task<Product?> GetBestProductMatchAsync(string ingredientName, List<Product> availableProducts)
        {
            if (!availableProducts.Any()) return null;

            var productListStr = string.Join(", ", availableProducts.Select(p => $"{p.Id}: {p.Name}"));
            var prompt = $"'{ingredientName}' malzemesi için şu ürün listesinden en uygun olanın ID'sini döndür: {productListStr}. Sadece ID'yi döndür, başka bir metin yazma.";

            try
            {
                var response = await _client.Models.GenerateContentAsync(_modelName, prompt);
                var matchedId = response.Candidates[0].Content.Parts[0].Text.Trim();
                return availableProducts.FirstOrDefault(p => p.Id == matchedId);
            }
            catch (Exception)
            {
                return null;
            }
        }

        private RecipeAnalysisResult? ParseJsonResponse(string json)
        {
            try
            {
                // Remove markdown code blocks if present
                if (json.Contains("```json"))
                {
                    json = json.Substring(json.IndexOf("```json") + 7);
                    json = json.Substring(0, json.LastIndexOf("```"));
                }
                else if (json.Contains("```"))
                {
                    json = json.Substring(json.IndexOf("```") + 3);
                    json = json.Substring(0, json.LastIndexOf("```"));
                }

                return JsonSerializer.Deserialize<RecipeAnalysisResult>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            }
            catch
            {
                return null;
            }
        }
    }
}
