#!/usr/bin/env python3
"""
=== MASTER PIPELINE ORCHESTRATOR ===
Version: 1.0.0 | Created: 2025-09-09

PURPOSE: 
Complete end-to-end cold outreach pipeline orchestration with creator-developer iteration cycle

CREATOR VISION:
- Seamless flow from raw leads to campaign-ready icebreakers
- Each stage validates and improves the next
- 11/10 quality assurance throughout the pipeline
- Complete logging and versioning for production reliability

DEVELOPER IMPLEMENTATION:
- Orchestrates all processors in correct sequence
- Validates data quality between stages
- Handles errors gracefully with detailed logging
- Provides comprehensive reporting and analytics

USAGE:
python master_pipeline.py input.csv --offer "Your offer description"
python master_pipeline.py --test                      # Test mode with sample data  
python master_pipeline.py --continue stage3.json     # Continue from specific stage
"""

import os
import sys
import json
import csv
import time
import argparse
from datetime import datetime
from pathlib import Path

# Import all processors
from company_name_cleaner_analytics import CompanyNameCleanerAnalytics
from website_intelligence_processor import WebsiteIntelligenceProcessor  
from personalization_extractor import PersonalizationExtractor
from icebreaker_generator import IcebreakerGenerator

# Pipeline orchestrator statistics
PIPELINE_STATS = {
    "version": "1.0.0",
    "created": "2025-09-09",
    "total_runs": 0,
    "companies_processed": 0,
    "complete_successes": 0,
    "partial_successes": 0,
    "total_failures": 0,
    "avg_processing_time_minutes": 0.0,
    "avg_cost_per_company": 0.0,
    "last_updated": None,
    "changelog": {
        "1.0.0": "Initial master pipeline with creator-developer iteration cycle"
    }
}

class MasterPipeline:
    """Complete cold outreach pipeline orchestrator"""
    
    def __init__(self, offer_details=None):
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "companies_processed": 0,
            "stage_results": {
                "name_cleaning": {"attempted": 0, "successful": 0},
                "website_intelligence": {"attempted": 0, "successful": 0},
                "personalization": {"attempted": 0, "successful": 0},
                "icebreaker_generation": {"attempted": 0, "successful": 0}
            },
            "total_cost_usd": 0.0,
            "processing_time_seconds": 0.0,
            "quality_scores": [],
            "errors": [],
            "company_results": []
        }
        
        self.offer_details = offer_details or "AI automation solutions that help agencies scale operations and improve client results"
        self.start_time = time.time()
        
        # Initialize processors
        try:
            print(f"Initializing Master Pipeline v{PIPELINE_STATS['version']}...")
            self.name_cleaner = CompanyNameCleanerAnalytics()
            self.website_processor = WebsiteIntelligenceProcessor()
            self.personalization_extractor = PersonalizationExtractor()
            self.icebreaker_generator = IcebreakerGenerator()
            print("All processors initialized successfully")
        except Exception as e:
            print(f"Critical error initializing processors: {str(e)}")
            raise
    
    def process_single_company(self, company_data):
        """
        Process a single company through the complete pipeline
        
        Args:
            company_data: Dict with company_name, company_domain, contact_name (optional)
            
        Returns:
            Dict with complete processing results
        """
        company_start_time = time.time()
        company_name = company_data.get('company_name', '').strip()
        domain = company_data.get('company_domain', '').strip()
        contact_name = company_data.get('contact_name', '').strip()
        
        # Clean domain format
        domain = domain.replace('http://', '').replace('https://', '').strip('/')
        
        result = {
            'input_data': company_data,
            'company_name': company_name,
            'domain': domain,
            'contact_name': contact_name,
            'pipeline_stages': {},
            'final_output': {},
            'processing_stats': {
                'stages_completed': 0,
                'total_stages': 4,
                'processing_time_seconds': 0,
                'total_cost_usd': 0.0,
                'quality_score': 0.0,
                'success': False,
                'errors': []
            }
        }
        
        print(f"\n{'='*60}")
        print(f"🎯 Processing: {company_name} ({domain})")
        print(f"{'='*60}")
        
        try:
            # STAGE 1: Company Name Cleaning
            print("\n1️⃣ STAGE 1: Company Name Cleaning")
            self.stats["stage_results"]["name_cleaning"]["attempted"] += 1
            
            try:
                cleaned_name = self.name_cleaner.clean_single_name(company_name)
                result['pipeline_stages']['name_cleaning'] = {
                    'original_name': company_name,
                    'cleaned_name': cleaned_name,
                    'success': True,
                    'processing_time': 0.1  # Minimal time for name cleaning
                }
                self.stats["stage_results"]["name_cleaning"]["successful"] += 1
                result['processing_stats']['stages_completed'] += 1
                print(f"   ✅ {company_name} → {cleaned_name}")
            except Exception as e:
                error_msg = f"Name cleaning failed: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return result
            
            # STAGE 2: Website Intelligence
            print("\n2️⃣ STAGE 2: Website Intelligence Discovery & Analysis")
            self.stats["stage_results"]["website_intelligence"]["attempted"] += 1
            
            try:
                website_result = self.website_processor.process_company(domain, company_name)
                result['pipeline_stages']['website_intelligence'] = website_result
                
                if website_result['processing_stats']['success']:
                    self.stats["stage_results"]["website_intelligence"]["successful"] += 1
                    result['processing_stats']['stages_completed'] += 1
                    result['processing_stats']['total_cost_usd'] += website_result['processing_stats'].get('api_cost_usd', 0)
                    print(f"   ✅ Website intelligence extracted successfully")
                    print(f"      📊 {len(website_result['all_pages_discovered'])} pages discovered")
                    print(f"      🎯 {len(website_result['selected_pages'])} pages selected for analysis")
                    print(f"      📄 {len(website_result['raw_content_data'])} pages scraped")
                else:
                    error_msg = f"Website intelligence failed: {website_result['processing_stats']['errors']}"
                    result['processing_stats']['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    return result
                    
            except Exception as e:
                error_msg = f"Website intelligence failed: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return result
            
            # STAGE 3: Personalization Extraction
            print("\n3️⃣ STAGE 3: Personalization Insights Extraction")
            self.stats["stage_results"]["personalization"]["attempted"] += 1
            
            try:
                personalization_result = self.personalization_extractor.extract_insights(
                    website_result['raw_content_data'],
                    company_name,
                    contact_name
                )
                result['pipeline_stages']['personalization'] = personalization_result
                
                if personalization_result['processing_stats']['success']:
                    self.stats["stage_results"]["personalization"]["successful"] += 1
                    result['processing_stats']['stages_completed'] += 1
                    result['processing_stats']['total_cost_usd'] += personalization_result['processing_stats']['api_cost_usd']
                    
                    insights_count = personalization_result['processing_stats']['insights_extracted']
                    print(f"   ✅ Extracted {insights_count} personalization insights")
                    
                    # Show top insights
                    for i, insight in enumerate(personalization_result['personalization_insights'][:2], 1):
                        value = insight.get('personalization_value', 'UNKNOWN')
                        text = insight.get('insight', '')[:80] + "..."
                        print(f"      {i}. [{value}] {text}")
                else:
                    error_msg = f"Personalization extraction failed: {personalization_result['processing_stats']['errors']}"
                    result['processing_stats']['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    return result
                    
            except Exception as e:
                error_msg = f"Personalization extraction failed: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return result
            
            # STAGE 4: Icebreaker Generation
            print("\n4️⃣ STAGE 4: Icebreaker Generation")
            self.stats["stage_results"]["icebreaker_generation"]["attempted"] += 1
            
            try:
                icebreaker_result = self.icebreaker_generator.generate_icebreakers(
                    personalization_result,
                    contact_name,
                    company_name,
                    self.offer_details
                )
                result['pipeline_stages']['icebreaker_generation'] = icebreaker_result
                
                if icebreaker_result['processing_stats']['success']:
                    self.stats["stage_results"]["icebreaker_generation"]["successful"] += 1
                    result['processing_stats']['stages_completed'] += 1
                    result['processing_stats']['total_cost_usd'] += icebreaker_result['processing_stats']['api_cost_usd']
                    
                    icebreakers_count = icebreaker_result['processing_stats']['icebreakers_generated']
                    recommended = icebreaker_result.get('recommended_version', 'A')
                    print(f"   ✅ Generated {icebreakers_count} icebreaker variations")
                    print(f"      🎯 Recommended version: {recommended}")
                    
                    # Show icebreakers
                    for icebreaker in icebreaker_result['icebreakers']:
                        version = icebreaker.get('version', '?')
                        response_rate = icebreaker.get('expected_response_rate', 'UNKNOWN')
                        text = icebreaker.get('icebreaker_text', '')
                        print(f"      {version} [{response_rate}]: {text[:100]}...")
                        
                    # Prepare final output
                    result['final_output'] = {
                        'company_name': company_name,
                        'cleaned_name': result['pipeline_stages']['name_cleaning']['cleaned_name'],
                        'contact_name': contact_name,
                        'domain': domain,
                        'icebreaker_variations': icebreaker_result['icebreakers'],
                        'recommended_version': icebreaker_result.get('recommended_version', 'A'),
                        'personalization_summary': icebreaker_result.get('overall_strategy', ''),
                        'insights_used': len(personalization_result['personalization_insights']),
                        'pages_analyzed': len(website_result['raw_content_data']),
                        'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    result['processing_stats']['success'] = True
                else:
                    error_msg = f"Icebreaker generation failed: {icebreaker_result['processing_stats']['errors']}"
                    result['processing_stats']['errors'].append(error_msg)
                    print(f"   ❌ {error_msg}")
                    return result
                    
            except Exception as e:
                error_msg = f"Icebreaker generation failed: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"   ❌ {error_msg}")
                return result
            
            # Calculate quality score (creator-developer iteration)
            quality_score = self._calculate_quality_score(result)
            result['processing_stats']['quality_score'] = quality_score
            self.stats["quality_scores"].append(quality_score)
            
            print(f"\n🎯 PIPELINE COMPLETE")
            print(f"   📊 Stages: {result['processing_stats']['stages_completed']}/{result['processing_stats']['total_stages']}")
            print(f"   💰 Cost: ${result['processing_stats']['total_cost_usd']:.4f}")
            print(f"   ⭐ Quality Score: {quality_score:.1f}/10")
            
            if quality_score >= 8.0:
                print(f"   🏆 EXCELLENT quality - ready for outreach!")
            elif quality_score >= 6.0:
                print(f"   ✅ GOOD quality - minor improvements possible")
            else:
                print(f"   ⚠️  NEEDS IMPROVEMENT - consider refining")
                
        except Exception as e:
            error_msg = f"Critical pipeline error: {str(e)}"
            result['processing_stats']['errors'].append(error_msg)
            self.stats["errors"].append(error_msg)
            print(f"💥 CRITICAL ERROR: {error_msg}")
        
        # Calculate final processing stats
        processing_time = time.time() - company_start_time
        result['processing_stats']['processing_time_seconds'] = processing_time
        self.stats["processing_time_seconds"] += processing_time
        self.stats["total_cost_usd"] += result['processing_stats']['total_cost_usd']
        
        # Update global stats
        self.stats["companies_processed"] += 1
        self.stats["company_results"].append({
            'company_name': company_name,
            'stages_completed': result['processing_stats']['stages_completed'],
            'success': result['processing_stats']['success'],
            'processing_time': processing_time,
            'cost': result['processing_stats']['total_cost_usd'],
            'quality_score': result['processing_stats']['quality_score']
        })
        
        if result['processing_stats']['success']:
            print(f"🎉 SUCCESS: Complete pipeline finished in {processing_time:.2f}s")
        else:
            print(f"⚠️  PARTIAL: Pipeline completed {result['processing_stats']['stages_completed']}/4 stages")
        
        return result
    
    def _calculate_quality_score(self, result):
        """Calculate quality score for creator-developer iteration"""
        score = 0.0
        max_score = 10.0
        
        # Stage completion (40% of score)
        stage_score = (result['processing_stats']['stages_completed'] / result['processing_stats']['total_stages']) * 4.0
        score += stage_score
        
        # Content quality (30% of score)
        try:
            if 'personalization' in result['pipeline_stages']:
                insights = result['pipeline_stages']['personalization']['personalization_insights']
                high_value_insights = sum(1 for i in insights if i.get('personalization_value') == 'HIGH')
                content_score = min(3.0, (high_value_insights / max(1, len(insights))) * 3.0)
                score += content_score
        except:
            pass
            
        # Icebreaker quality (30% of score)
        try:
            if 'icebreaker_generation' in result['pipeline_stages']:
                icebreakers = result['pipeline_stages']['icebreaker_generation']['icebreakers']
                high_response_rate = sum(1 for i in icebreakers if i.get('expected_response_rate') == 'HIGH')
                icebreaker_score = min(3.0, (high_response_rate / max(1, len(icebreakers))) * 3.0)
                score += icebreaker_score
        except:
            pass
        
        return min(score, max_score)
    
    def process_csv_batch(self, csv_path, limit=None):
        """Process companies from CSV file"""
        print(f"\n🔄 Processing CSV batch: {csv_path}")
        
        results = []
        processed_count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    if limit and processed_count >= limit:
                        print(f"📊 Reached processing limit of {limit} companies")
                        break
                    
                    # Extract company data
                    company_data = {
                        'company_name': row.get('company_name', '').strip(),
                        'company_domain': row.get('company_domain', '').strip(),
                        'contact_name': row.get('first_name', '').strip() + ' ' + row.get('last_name', '').strip()
                    }
                    
                    if not company_data['company_name'] or not company_data['company_domain']:
                        print(f"⚠️  Skipping row - missing required data")
                        continue
                    
                    result = self.process_single_company(company_data)
                    results.append(result)
                    processed_count += 1
                    
                    # Brief pause between companies
                    time.sleep(2)
                    
        except Exception as e:
            print(f"💥 Error processing CSV: {str(e)}")
            
        return results
    
    def save_results(self, results, output_dir=None):
        """Save complete pipeline results"""
        if output_dir is None:
            output_dir = "../../leads/ready"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(output_dir, exist_ok=True)
        
        # Save complete JSON results
        json_path = os.path.join(output_dir, f"pipeline_results_{timestamp}.json")
        output_data = {
            'metadata': {
                'pipeline_version': PIPELINE_STATS['version'],
                'generated_at': datetime.now().isoformat(),
                'offer_details': self.offer_details,
                'total_companies': len(results),
                'session_stats': self.stats,
                'global_stats': PIPELINE_STATS
            },
            'results': results
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Complete results saved to: {json_path}")
        
        # Save campaign-ready CSV
        csv_path = os.path.join(output_dir, f"campaign_ready_{timestamp}.csv")
        self._save_campaign_csv(results, csv_path)
        
        return json_path, csv_path
    
    def _save_campaign_csv(self, results, csv_path):
        """Save campaign-ready CSV file"""
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'company_name', 'cleaned_name', 'contact_name', 'domain',
                'icebreaker_a', 'icebreaker_a_response_rate',
                'icebreaker_b', 'icebreaker_b_response_rate', 
                'icebreaker_c', 'icebreaker_c_response_rate',
                'recommended_version', 'personalization_summary',
                'insights_count', 'pages_analyzed', 'quality_score',
                'processing_success', 'generation_date'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                if not result['processing_stats']['success']:
                    # Write failed records too for tracking
                    writer.writerow({
                        'company_name': result.get('company_name', ''),
                        'domain': result.get('domain', ''),
                        'processing_success': False,
                        'generation_date': datetime.now().strftime('%Y-%m-%d')
                    })
                    continue
                
                final_output = result.get('final_output', {})
                icebreakers = final_output.get('icebreaker_variations', [])
                
                # Extract up to 3 icebreakers
                icebreaker_data = {}
                for i, icebreaker in enumerate(icebreakers[:3]):
                    version = ['a', 'b', 'c'][i]
                    icebreaker_data[f'icebreaker_{version}'] = icebreaker.get('icebreaker_text', '')
                    icebreaker_data[f'icebreaker_{version}_response_rate'] = icebreaker.get('expected_response_rate', 'UNKNOWN')
                
                # Fill missing variations
                for version in ['a', 'b', 'c']:
                    if f'icebreaker_{version}' not in icebreaker_data:
                        icebreaker_data[f'icebreaker_{version}'] = ''
                        icebreaker_data[f'icebreaker_{version}_response_rate'] = ''
                
                writer.writerow({
                    'company_name': final_output.get('company_name', ''),
                    'cleaned_name': final_output.get('cleaned_name', ''),
                    'contact_name': final_output.get('contact_name', ''),
                    'domain': final_output.get('domain', ''),
                    'icebreaker_a': icebreaker_data.get('icebreaker_a', ''),
                    'icebreaker_a_response_rate': icebreaker_data.get('icebreaker_a_response_rate', ''),
                    'icebreaker_b': icebreaker_data.get('icebreaker_b', ''),
                    'icebreaker_b_response_rate': icebreaker_data.get('icebreaker_b_response_rate', ''),
                    'icebreaker_c': icebreaker_data.get('icebreaker_c', ''),
                    'icebreaker_c_response_rate': icebreaker_data.get('icebreaker_c_response_rate', ''),
                    'recommended_version': final_output.get('recommended_version', ''),
                    'personalization_summary': final_output.get('personalization_summary', ''),
                    'insights_count': final_output.get('insights_used', 0),
                    'pages_analyzed': final_output.get('pages_analyzed', 0),
                    'quality_score': result['processing_stats']['quality_score'],
                    'processing_success': True,
                    'generation_date': final_output.get('generation_date', '')
                })
        
        print(f"📊 Campaign-ready CSV saved to: {csv_path}")
    
    def generate_session_report(self):
        """Generate comprehensive session report"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*80}")
        print(f"🎯 MASTER PIPELINE - COMPREHENSIVE SESSION REPORT")
        print(f"{'='*80}")
        print(f"📊 Companies Processed: {self.stats['companies_processed']}")
        print(f"⏱️  Total Processing Time: {total_time/60:.1f} minutes")
        print(f"💰 Total Cost: ${self.stats['total_cost_usd']:.4f}")
        
        # Stage-by-stage breakdown
        print(f"\n📈 STAGE-BY-STAGE PERFORMANCE:")
        for stage_name, stage_stats in self.stats['stage_results'].items():
            attempted = stage_stats['attempted']
            successful = stage_stats['successful']
            success_rate = (successful / attempted * 100) if attempted > 0 else 0
            print(f"   {stage_name.replace('_', ' ').title()}: {successful}/{attempted} ({success_rate:.1f}%)")
        
        # Quality metrics
        if self.stats['quality_scores']:
            avg_quality = sum(self.stats['quality_scores']) / len(self.stats['quality_scores'])
            print(f"\n⭐ QUALITY METRICS:")
            print(f"   Average Quality Score: {avg_quality:.1f}/10")
            print(f"   Excellent Quality (8.0+): {sum(1 for s in self.stats['quality_scores'] if s >= 8.0)} companies")
            print(f"   Good Quality (6.0+): {sum(1 for s in self.stats['quality_scores'] if s >= 6.0)} companies")
        
        # Performance metrics
        if self.stats['companies_processed'] > 0:
            avg_time = total_time / self.stats['companies_processed']
            avg_cost = self.stats['total_cost_usd'] / self.stats['companies_processed']
            complete_successes = sum(1 for r in self.stats['company_results'] if r['success'])
            success_rate = complete_successes / self.stats['companies_processed'] * 100
            
            print(f"\n📊 PERFORMANCE METRICS:")
            print(f"   Average Time per Company: {avg_time/60:.1f} minutes")
            print(f"   Average Cost per Company: ${avg_cost:.4f}")
            print(f"   Complete Success Rate: {success_rate:.1f}%")
            print(f"   Complete Successes: {complete_successes}")
            print(f"   Partial Successes: {self.stats['companies_processed'] - complete_successes}")
        
        # Error summary
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][-5:]:  # Show last 5 errors
                print(f"   • {error}")
        
        print(f"\n🎯 CREATOR-DEVELOPER ITERATION RESULTS:")
        if self.stats['quality_scores']:
            excellent = sum(1 for s in self.stats['quality_scores'] if s >= 8.0)
            good = sum(1 for s in self.stats['quality_scores'] if s >= 6.0)
            needs_work = len(self.stats['quality_scores']) - good
            
            print(f"   🏆 Excellent (8.0+): {excellent} companies ({excellent/len(self.stats['quality_scores'])*100:.1f}%)")
            print(f"   ✅ Good (6.0+): {good} companies ({good/len(self.stats['quality_scores'])*100:.1f}%)")
            print(f"   ⚠️  Needs Work: {needs_work} companies ({needs_work/len(self.stats['quality_scores'])*100:.1f}%)")
            
            if excellent / len(self.stats['quality_scores']) >= 0.7:
                print(f"   🎉 CREATOR VISION ACHIEVED: 70%+ excellent quality!")
            elif good / len(self.stats['quality_scores']) >= 0.8:
                print(f"   ✅ STRONG PERFORMANCE: 80%+ good quality")
            else:
                print(f"   🔧 ITERATION NEEDED: Quality improvements required")
        
        print(f"{'='*80}")
        
        # Update global stats
        PIPELINE_STATS["total_runs"] += 1
        PIPELINE_STATS["companies_processed"] += self.stats['companies_processed']
        complete_successes = sum(1 for r in self.stats['company_results'] if r['success'])
        PIPELINE_STATS["complete_successes"] += complete_successes
        PIPELINE_STATS["partial_successes"] += (self.stats['companies_processed'] - complete_successes)
        PIPELINE_STATS["last_updated"] = datetime.now().isoformat()
        
        if PIPELINE_STATS["companies_processed"] > 0:
            PIPELINE_STATS["avg_processing_time_minutes"] = total_time / PIPELINE_STATS["companies_processed"] / 60
            PIPELINE_STATS["avg_cost_per_company"] = self.stats['total_cost_usd'] / self.stats['companies_processed']


def main():
    parser = argparse.ArgumentParser(description='Master Cold Outreach Pipeline')
    parser.add_argument('input', nargs='?', help='Input CSV file or --test for test mode')
    parser.add_argument('--offer', type=str, help='Offer description for icebreakers')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--test', action='store_true', help='Run in test mode with sample data')
    parser.add_argument('--continue', dest='continue_file', help='Continue from previous stage JSON file')
    
    args = parser.parse_args()
    
    # Determine offer details
    offer_details = args.offer or "AI automation solutions that help agencies scale operations and improve client results"
    
    # Initialize pipeline
    pipeline = MasterPipeline(offer_details)
    
    try:
        if args.test:
            print("🧪 Running in test mode...")
            # Test with sample company
            test_company = {
                'company_name': 'Stryve Digital Marketing',
                'company_domain': 'stryvemarketing.com',
                'contact_name': 'Grace Cole'
            }
            results = [pipeline.process_single_company(test_company)]
            
        elif args.continue_file:
            print(f"🔄 Continuing from: {args.continue_file}")
            # Load previous results and continue from specific stage
            # Implementation would depend on specific continuation logic
            print("⚠️  Continue functionality not implemented yet")
            return
            
        elif args.input and os.path.exists(args.input):
            print(f"📁 Processing CSV file: {args.input}")
            results = pipeline.process_csv_batch(args.input, args.limit)
            
        else:
            print("❌ Please provide input CSV file or use --test mode")
            parser.print_help()
            return
        
        # Save results
        if results:
            json_path, csv_path = pipeline.save_results(results)
            print(f"\n💾 Results saved:")
            print(f"   📄 Complete data: {json_path}")
            print(f"   📊 Campaign CSV: {csv_path}")
        
        # Generate comprehensive report
        pipeline.generate_session_report()
        
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user")
        print("💾 Saving partial results...")
        if 'results' in locals() and results:
            pipeline.save_results(results)
            pipeline.generate_session_report()
            
    except Exception as e:
        print(f"💥 Critical pipeline error: {str(e)}")
        raise


if __name__ == "__main__":
    main()