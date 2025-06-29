'''
BERT-Based File Recovery System
Uses pretrained BERT models for text file corruption and recovery
'''

import os
import random
import torch
from transformers import BertTokenizer, BertForMaskedLM, AutoTokenizer, AutoModelForMaskedLM
from pathlib import Path
from hashlib import sha256
import time

class BERTFileRecovery:
    """
    BERT-based file recovery system for text files
    """
    
    def __init__(self, model_name='bert-base-uncased'):
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Initializing BERT File Recovery with {model_name}")
        print(f"Using device: {self.device}")
        
        # Load pretrained model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForMaskedLM.from_pretrained(model_name).to(self.device)
            self.model.eval()
            print(f"✅ Successfully loaded {model_name}")
        except Exception as e:
            print(f"❌ Error loading {model_name}: {e}")
            print("Falling back to bert-base-uncased...")
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            self.model = BertForMaskedLM.from_pretrained('bert-base-uncased').to(self.device)
            self.model.eval()
    
    def corrupt_text_file(self, input_file, output_file, corruption_level=0.15):
        """
        Corrupt a text file by masking random words
        
        Args:
            input_file: Path to input text file
            output_file: Path to corrupted output file
            corruption_level: Percentage of words to mask (0.0 to 1.0)
        """
        print(f"Corrupting text file: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Split into sentences for better processing
            sentences = text.split('. ')
            corrupted_sentences = []
            
            for sentence in sentences:
                if sentence.strip():
                    corrupted_sentence = self._corrupt_sentence(sentence, corruption_level)
                    corrupted_sentences.append(corrupted_sentence)
            
            corrupted_text = '. '.join(corrupted_sentences)
            
            # Write corrupted file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(corrupted_text)
            
            print(f"✅ Corrupted file saved to: {output_file}")
            print(f"   Original length: {len(text)} characters")
            print(f"   Corrupted length: {len(corrupted_text)} characters")
            
            return len(corrupted_text)
            
        except Exception as e:
            print(f"❌ Error corrupting file: {e}")
            return 0
    
    def _corrupt_sentence(self, sentence, corruption_level):
        """
        Corrupt a single sentence by masking words
        """
        words = sentence.split()
        if len(words) == 0:
            return sentence
        
        num_to_mask = max(1, int(len(words) * corruption_level))
        mask_indices = random.sample(range(len(words)), min(num_to_mask, len(words)))
        
        corrupted_words = words.copy()
        for idx in mask_indices:
            corrupted_words[idx] = self.tokenizer.mask_token
        
        return ' '.join(corrupted_words)
    
    def recover_text_file(self, corrupted_file, recovered_file):
        """
        Recover a corrupted text file using BERT
        
        Args:
            corrupted_file: Path to corrupted text file
            recovered_file: Path to recovered output file
        """
        print(f"Recovering text file: {corrupted_file}")
        
        try:
            with open(corrupted_file, 'r', encoding='utf-8') as f:
                corrupted_text = f.read()
            
            # Split into sentences for processing
            sentences = corrupted_text.split('. ')
            recovered_sentences = []
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    print(f"Processing sentence {i+1}/{len(sentences)}...")
                    recovered_sentence = self._recover_sentence(sentence)
                    recovered_sentences.append(recovered_sentence)
            
            recovered_text = '. '.join(recovered_sentences)
            
            # Write recovered file
            with open(recovered_file, 'w', encoding='utf-8') as f:
                f.write(recovered_text)
            
            print(f"✅ Recovered file saved to: {recovered_file}")
            return len(recovered_text)
            
        except Exception as e:
            print(f"❌ Error recovering file: {e}")
            return 0
    
    def _recover_sentence(self, sentence):
        """
        Recover a single sentence using BERT
        """
        try:
            # Tokenize the sentence
            inputs = self.tokenizer(sentence, return_tensors='pt', truncation=True, max_length=512)
            input_ids = inputs['input_ids'].to(self.device)
            
            # Find mask tokens
            mask_token_index = (input_ids == self.tokenizer.mask_token_id)[0].nonzero(as_tuple=True)[0]
            
            if len(mask_token_index) == 0:
                return sentence  # No masks to recover
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Replace masks with predictions
            recovered_ids = input_ids.clone()
            for idx in mask_token_index:
                mask_logits = logits[0, idx]
                predicted_token_id = mask_logits.argmax().item()
                recovered_ids[0, idx] = predicted_token_id
            
            # Decode back to text
            recovered_text = self.tokenizer.decode(recovered_ids[0], skip_special_tokens=True)
            return recovered_text
            
        except Exception as e:
            print(f"  ⚠️ Error recovering sentence: {e}")
            return sentence  # Return original if recovery fails
    
    def compare_files(self, original_file, recovered_file):
        """
        Compare original and recovered files
        """
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            with open(recovered_file, 'r', encoding='utf-8') as f:
                recovered_text = f.read()
            
            # Calculate similarity
            original_words = original_text.split()
            recovered_words = recovered_text.split()
            
            min_len = min(len(original_words), len(recovered_words))
            if min_len == 0:
                return False, 0.0
            
            match_count = sum(1 for i in range(min_len) if original_words[i] == recovered_words[i])
            similarity = match_count / min_len
            
            # Calculate hashes
            original_hash = sha256(original_text.encode()).hexdigest()
            recovered_hash = sha256(recovered_text.encode()).hexdigest()
            
            print(f"\n📊 File Comparison Results:")
            print(f"   Original hash: {original_hash[:16]}...")
            print(f"   Recovered hash: {recovered_hash[:16]}...")
            print(f"   Files match exactly: {original_hash == recovered_hash}")
            print(f"   Word similarity: {similarity*100:.1f}% ({match_count}/{min_len} words)")
            
            return original_hash == recovered_hash, similarity
            
        except Exception as e:
            print(f"❌ Error comparing files: {e}")
            return False, 0.0
    
    def batch_recover_files(self, input_dir, output_dir, file_pattern="*.txt"):
        """
        Batch recover multiple text files in a directory
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        files = list(input_path.glob(file_pattern))
        print(f"Found {len(files)} files to process")
        
        results = []
        for i, file_path in enumerate(files):
            print(f"\nProcessing file {i+1}/{len(files)}: {file_path.name}")
            
            # Create corrupted version
            corrupted_file = output_path / f"corrupted_{file_path.name}"
            self.corrupt_text_file(str(file_path), str(corrupted_file))
            
            # Recover the corrupted file
            recovered_file = output_path / f"recovered_{file_path.name}"
            self.recover_text_file(str(corrupted_file), str(recovered_file))
            
            # Compare results
            exact_match, similarity = self.compare_files(str(file_path), str(recovered_file))
            results.append({
                'file': file_path.name,
                'exact_match': exact_match,
                'similarity': similarity
            })
        
        # Print summary
        print(f"\n📈 Batch Recovery Summary:")
        print(f"   Total files processed: {len(results)}")
        print(f"   Exact matches: {sum(1 for r in results if r['exact_match'])}")
        print(f"   Average similarity: {sum(r['similarity'] for r in results)/len(results)*100:.1f}%")
        
        return results

def main():
    """
    Demo of BERT-based file recovery
    """
    print("BERT File Recovery System Demo")
    print("=" * 50)
    
    # Initialize recovery system
    recovery_system = BERTFileRecovery()
    
    # Create test files
    test_files = [
        ("document1.txt", "This is a sample document for testing BERT-based file recovery. The system should be able to recover masked words in the text. This demonstrates the power of pretrained language models in file corruption recovery."),
        ("document2.txt", "Another test document with different content. It contains technical terms like machine learning, artificial intelligence, and natural language processing. The BERT model should handle these terms well."),
        ("document3.txt", "A longer document with multiple sentences. Each sentence contains different types of words and punctuation. The recovery system will process each sentence individually to maximize accuracy.")
    ]
    
    # Create test files
    for filename, content in test_files:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created test file: {filename}")
    
    print(f"\n🚀 Starting file recovery demo...")
    
    # Process each test file
    for filename, _ in test_files:
        print(f"\n{'='*30}")
        print(f"Processing: {filename}")
        print(f"{'='*30}")
        
        # Corrupt the file
        corrupted_file = f"corrupted_{filename}"
        recovery_system.corrupt_text_file(filename, corrupted_file, corruption_level=0.2)
        
        # Recover the file
        recovered_file = f"recovered_{filename}"
        recovery_system.recover_text_file(corrupted_file, recovered_file)
        
        # Compare results
        recovery_system.compare_files(filename, recovered_file)
    
    print(f"\n✅ Demo completed! Check the generated files:")
    print(f"   - Original files: document1.txt, document2.txt, document3.txt")
    print(f"   - Corrupted files: corrupted_*.txt")
    print(f"   - Recovered files: recovered_*.txt")

if __name__ == "__main__":
    main() 