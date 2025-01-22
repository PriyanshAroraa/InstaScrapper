import instaloader
import json
import google.generativeai as genai
import time
import random
from datetime import datetime
import os

# Configuration
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel(
    'models/gemini-1.5-pro-002',
    tools={'google_search_retrieval': {}},
    system_instruction="You are a professional social media analyst."
)

# Anti-blocking configuration
CUSTOM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.instagram.com/',
    'DNT': '1'
}

def safe_json_parse(text):
    """Robust JSON parsing with error recovery"""
    clean_text = text.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        try:
            start = max(clean_text.find('{'), clean_text.find('['))
            end = max(clean_text.rfind('}'), clean_text.rfind(']')) + 1
            return json.loads(clean_text[start:end])
        except:
            return {"error": "JSON parsing failed", "raw_response": clean_text[:200]}

def get_instagram_data(username):
    """Advanced Instagram scraper with anti-blocking features"""
    L = instaloader.Instaloader(
        user_agent=CUSTOM_HEADERS['User-Agent'],
        sleep=True,
        quiet=True,
        request_timeout=45,
        max_connection_attempts=3
    )
    
    try:
        # Randomized delay pattern
        time.sleep(random.uniform(0.5, 2.5))
        
        # Configure session
        L.context._session.headers.update(CUSTOM_HEADERS)
        L.context._session.verify = True  # Enable SSL verification
        
        profile = instaloader.Profile.from_username(L.context, username)
        
        if profile.is_private:
            return {"error": f"Private profile @{username}"}

        # Limited post collection with randomized intervals
        posts = []
        for i, post in enumerate(profile.get_posts()):
            if i >= 3:  # Only get 3 posts
                break
            posts.append({
                "id": post.shortcode,
                "likes": post.likes,
                "comments": post.comments,
                "caption": post.caption,
                "type": "video" if post.is_video else "image",
                "timestamp": post.date_utc.isoformat()
            })
            time.sleep(random.uniform(1.8, 4.2))

        return {
            "username": profile.username,
            "full_name": profile.full_name,
            "bio": profile.biography,
            "followers": profile.followers,
            "following": profile.followees,
            "posts_count": profile.mediacount,
            "profile_pic": profile.profile_pic_url,
            "is_verified": profile.is_verified,
            "recent_posts": posts,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except instaloader.exceptions.QueryReturnedBadRequestException:
        return {"error": "Instagram API blocked - try again later"}
    except instaloader.exceptions.ConnectionException as e:
        return {"error": f"Connection issue: {str(e)}"}
    except Exception as e:
        return {"error": f"Scraping error: {str(e)}"}

def generate_company_report(instagram_data):
    """Generate company profile from Instagram data"""
    analysis_prompt = f"""
    Analyze this social media profile to create detailed company report:
    {json.dumps(instagram_data, indent=2)}
    
    Include in JSON format:
    - company_name
    - industry
    - core_offerings (list)
    - target_demographics
    - unique_value_proposition
    - brand_voice
    - estimated_team_size
    - geographic_operation
    - content_strategy_analysis
    """
    
    try:
        response = model.generate_content(analysis_prompt)
        report = safe_json_parse(response.text)
        return report
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def find_competitors(company_report):
    """Find competitors using Google-grounded search"""
    prompt = f"""
    Based on this company profile, identify top competitors with Instagram handles.
    Use Google Search grounding for accuracy. Return JSON format:
    {{
        "competitors": [
            {{
                "name": "",
                "industry_match": "",
                "instagram": "",
                "competition_level": "high/medium/low",
                "reason": ""
            }}
        ]
    }}
    
    Company Profile:
    {json.dumps(company_report, indent=2)}
    """
    
    try:
        response = model.generate_content(prompt)
        return safe_json_parse(response.text).get("competitors", [])
    except Exception as e:
        return []

def analyze_performance(data):
    """Generate performance insights"""
    prompt = f"""
    Analyze social media performance metrics and generate insights:
    {json.dumps(data, indent=2)}
    
    Include in JSON:
    - engagement_rate
    - optimal_posting_times
    - content_type_breakdown
    - hashtag_performance
    - growth_strategy
    - improvement_recommendations
    """
    
    try:
        response = model.generate_content(prompt)
        return safe_json_parse(response.text)
    except Exception as e:
        return {"error": f"Performance analysis failed: {str(e)}"}

def main():
    # Start execution timer
    start_time = time.time()
    
    # Only change needed 👇 (public Instagram handle)
    TARGET_ACCOUNT = "nike"
    
    # Retry mechanism with exponential backoff
    max_retries = 3
    company_data = {}
    for attempt in range(max_retries):
        print(f"Attempt {attempt+1}/{max_retries} to collect data...")
        company_data = get_instagram_data(TARGET_ACCOUNT)
        if "error" not in company_data:
            break
        wait_time = 2 ** (attempt + 1) + random.uniform(0, 2)
        print(f"Waiting {wait_time:.1f} seconds before retry...")
        time.sleep(wait_time)
    
    if "error" in company_data:
        print(f"❌ Final error: {company_data['error']}")
        # Calculate total time even on error
        total_time = time.time() - start_time
        print(f"⏱️ Execution time: {total_time:.2f} seconds")
        return
    
    # Generate reports
    company_report = generate_company_report(company_data)
    competitors = find_competitors(company_report)
    
    # Analyze competitors
    competitor_analysis = []
    for comp in competitors[:2]:  # Limit to 2 competitors
        if comp.get('instagram'):
            print(f"Analyzing competitor: {comp['instagram']}")
            comp_data = get_instagram_data(comp['instagram'].lstrip('@'))
            if "error" not in comp_data:
                analysis = analyze_performance(comp_data)
                competitor_analysis.append({
                    "competitor_info": comp,
                    "data": comp_data,
                    "analysis": analysis
                })
            time.sleep(random.uniform(1, 3))
    
    # Generate final report
    final_report = {
        "target_analysis": analyze_performance(company_data),
        "company_profile": company_report,
        "competitor_insights": competitor_analysis,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Save results
    with open("social_media_auditokfinal.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    # Calculate and display total execution time
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = total_time % 60
    
    print("✅ Report generated: social_media_audit.json")
    print(f"⏱️ Total execution time: {minutes} minutes {seconds:.2f} seconds")

if __name__ == "__main__":
    main()
