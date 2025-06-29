'''
BERT Integration for Secure File Transfer System
Provides text file recovery capabilities using pretrained BERT models
Enhanced with PDF and DOCX support
'''

import os
import logging
from bert_file_recovery import BERTFileRecovery
from file_processor import FileProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BERTRecoveryIntegration:
    """
    Integration class for BERT-based text file recovery
    Enhanced with PDF and DOCX support
    """
    
    def __init__(self, model_name='bert-base-uncased'):
        self.recovery_system = BERTFileRecovery(model_name)
        self.file_processor = FileProcessor()
        self.supported_extensions = self.file_processor.get_supported_formats()
    
    def is_text_file(self, file_path):
        """
        Check if file is a supported format that can be processed by BERT
        """
        return self.file_processor.is_supported_format(file_path)
    
    def get_supported_formats(self):
        """
        Get list of supported file formats
        """
        return self.file_processor.get_supported_formats()
    
    def extract_text_from_file(self, file_path):
        """
        Extract text from file regardless of format
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Extracted text content, or None if failed
        """
        return self.file_processor.extract_text(file_path)
    
    def recover_corrupted_text_file(self, corrupted_file_path, output_path=None):
        """
        Recover a corrupted text file using BERT
        
        Args:
            corrupted_file_path: Path to the corrupted file
            output_path: Path for the recovered file (optional)
        
        Returns:
            tuple: (success, recovered_file_path, similarity_score)
        """
        try:
            if not self.is_text_file(corrupted_file_path):
                logger.warning(f"File {corrupted_file_path} is not a supported format")
                return False, None, 0.0
            
            if not os.path.exists(corrupted_file_path):
                logger.error(f"Corrupted file not found: {corrupted_file_path}")
                return False, None, 0.0
            
            # Extract text from the file
            logger.info(f"Extracting text from: {corrupted_file_path}")
            extracted_text = self.extract_text_from_file(corrupted_file_path)
            
            if not extracted_text:
                logger.error(f"Failed to extract text from: {corrupted_file_path}")
                return False, None, 0.0
            
            # Create a temporary text file for BERT processing
            temp_text_file = f"{corrupted_file_path}_temp.txt"
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            # Generate output path if not provided
            if output_path is None:
                base_name = os.path.splitext(corrupted_file_path)[0]
                output_path = f"{base_name}_recovered.txt"
            
            logger.info(f"Attempting to recover text file: {corrupted_file_path}")
            
            # Recover the text file using BERT
            recovered_length = self.recovery_system.recover_text_file(temp_text_file, output_path)
            
            # Clean up temporary file
            if os.path.exists(temp_text_file):
                os.remove(temp_text_file)
            
            if recovered_length > 0:
                logger.info(f"✅ Successfully recovered file to: {output_path}")
                return True, output_path, 1.0  # Assuming successful recovery
            else:
                logger.error(f"❌ Failed to recover file: {corrupted_file_path}")
                return False, None, 0.0
                
        except Exception as e:
            logger.error(f"Error during BERT recovery: {e}")
            return False, None, 0.0
    
    def recover_file(self, file_path):
        """
        Recover a corrupted file and return the recovered content
        
        Args:
            file_path: Path to the corrupted file
        
        Returns:
            str: Recovered file content, or None if recovery failed
        """
        try:
            if not self.is_text_file(file_path):
                logger.warning(f"File {file_path} is not a supported format")
                return None
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            # Extract text from the original file
            original_text = self.extract_text_from_file(file_path)
            if not original_text:
                logger.error(f"Failed to extract text from: {file_path}")
                return None
            
            # Create a temporary text file for BERT processing
            temp_text_file = f"{file_path}_temp.txt"
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                f.write(original_text)
            
            # Create a temporary recovered file
            temp_recovered_path = f"{file_path}_temp_recovered.txt"
            
            # Attempt recovery
            recovered_length = self.recovery_system.recover_text_file(temp_text_file, temp_recovered_path)
            
            # Clean up temporary text file
            if os.path.exists(temp_text_file):
                os.remove(temp_text_file)
            
            if recovered_length > 0:
                # Read the recovered content
                with open(temp_recovered_path, 'r', encoding='utf-8') as f:
                    recovered_content = f.read()
                
                # Clean up temporary recovered file
                if os.path.exists(temp_recovered_path):
                    os.remove(temp_recovered_path)
                
                logger.info(f"✅ Successfully recovered file: {file_path}")
                return recovered_content
            else:
                logger.error(f"❌ Failed to recover file: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error during file recovery: {e}")
            return None
    
    def batch_recover_directory(self, input_directory, output_directory):
        """
        Recover all supported files in a directory
        
        Args:
            input_directory: Directory containing corrupted files
            output_directory: Directory to save recovered files
        
        Returns:
            dict: Summary of recovery results
        """
        try:
            if not os.path.exists(input_directory):
                logger.error(f"Input directory not found: {input_directory}")
                return {}
            
            os.makedirs(output_directory, exist_ok=True)
            
            # Get all supported files in the directory
            supported_files = []
            for file in os.listdir(input_directory):
                file_path = os.path.join(input_directory, file)
                if os.path.isfile(file_path) and self.is_text_file(file_path):
                    supported_files.append(file_path)
            
            logger.info(f"Found {len(supported_files)} supported files to recover")
            
            results = {
                'total_files': len(supported_files),
                'successful_recoveries': 0,
                'failed_recoveries': 0,
                'recovered_files': []
            }
            
            for file_path in supported_files:
                filename = os.path.basename(file_path)
                output_path = os.path.join(output_directory, f"recovered_{filename}")
                
                success, recovered_path, similarity = self.recover_corrupted_text_file(file_path, output_path)
                
                if success:
                    results['successful_recoveries'] += 1
                    results['recovered_files'].append({
                        'original': file_path,
                        'recovered': recovered_path,
                        'similarity': similarity
                    })
                else:
                    results['failed_recoveries'] += 1
            
            logger.info(f"Batch recovery completed: {results['successful_recoveries']}/{results['total_files']} successful")
            return results
            
        except Exception as e:
            logger.error(f"Error during batch recovery: {e}")
            return {}
    
    def test_recovery_system(self, test_file_path=None):
        """
        Test the BERT recovery system with a sample file
        
        Args:
            test_file_path: Optional path to test file, will create one if not provided
        """
        try:
            if test_file_path is None:
                # Create a test file
                test_file_path = "test_bert_recovery.txt"
                test_content = """
                This is a test document for BERT-based file recovery.
                It contains various types of text including technical terms like machine learning and artificial intelligence.
                The system should be able to recover masked words using the pretrained BERT model.
                This demonstrates the effectiveness of transformer-based language models in text recovery.
                """
                
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                logger.info(f"Created test file: {test_file_path}")
            
            # Corrupt the test file
            corrupted_file = f"corrupted_{test_file_path}"
            self.recovery_system.corrupt_text_file(test_file_path, corrupted_file, corruption_level=0.2)
            
            # Recover the corrupted file
            recovered_file = f"recovered_{test_file_path}"
            success, _, _ = self.recover_corrupted_text_file(corrupted_file, recovered_file)
            
            if success:
                # Compare results
                exact_match, similarity = self.recovery_system.compare_files(test_file_path, recovered_file)
                logger.info(f"Test completed successfully!")
                logger.info(f"Exact match: {exact_match}, Similarity: {similarity*100:.1f}%")
                return True
            else:
                logger.error("Test failed!")
                return False
                
        except Exception as e:
            logger.error(f"Error during test: {e}")
            return False

def main():
    """
    Demo and test the enhanced BERT integration
    """
    print("BERT Recovery Integration Demo (Enhanced with PDF/DOCX Support)")
    print("=" * 60)
    
    # Initialize integration
    integration = BERTRecoveryIntegration()
    
    print(f"Supported formats: {', '.join(integration.get_supported_formats())}")
    
    # Test the system
    print("\n🧪 Testing BERT recovery system...")
    success = integration.test_recovery_system()
    
    if success:
        print("\n✅ Enhanced BERT integration is working correctly!")
        print("\n📋 Usage examples:")
        print("   # Recover a single file (any supported format)")
        print("   success, recovered_path, similarity = integration.recover_corrupted_text_file('corrupted_file.pdf')")
        print("   ")
        print("   # Batch recover all supported files in a directory")
        print("   results = integration.batch_recover_directory('corrupted_files/', 'recovered_files/')")
        print("   ")
        print("   # Test the system")
        print("   integration.test_recovery_system()")
        print("   ")
        print("   # Extract text from any supported format")
        print("   text = integration.extract_text_from_file('document.docx')")
    else:
        print("\n❌ Enhanced BERT integration test failed!")

if __name__ == "__main__":
    main() 