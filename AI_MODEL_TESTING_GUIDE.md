# AI Model Testing Guide - Quick Reference

## 🎯 Goal: Use Multiple AI Models to Validate Your Code

**Why use multiple models?**
- Different models catch different issues
- Cross-validation ensures accuracy
- Each model has unique strengths

---

## 🤖 Method 1: ChatGPT (Best for Code Quality)

### Access: https://chat.openai.com

### Copy-Paste Prompt:

```
I have a regulatory data lineage visualization system (FR 2590 SCCL report).
Please review this code for accuracy, performance, and best practices.

CONTEXT:
- Visualizes 494 nodes (20 sources, 75 atomic CDEs, 75 transformations, 75 CDEs, 198 MDRMs, 14 schedules, 1 endpoint)
- Creates 634 edges connecting the data flow
- Uses Python (pandas, pyvis) and JavaScript (vis.js)
- Expected behavior: All 198 MDRMs should trace back to sources

CURRENT ISSUE:
- Validation shows 123 MDRMs have no input connections
- Need to determine if this is a data issue or code issue

REVIEW FOCUS:
1. Is the Excel parsing logic correct?
2. Are node/edge creation algorithms accurate?
3. Any performance bottlenecks?
4. Missing error handling?
5. Code quality and maintainability?

CODE TO REVIEW:
[Paste integrate_excel_data_corrected.py here]

Please provide:
- Issues found (with severity)
- Specific code improvements
- Why 123 MDRMs might be missing inputs
```

---

## 🧠 Method 2: Claude (Best for Data Logic)

### Access: https://claude.ai

### Copy-Paste Prompt:

```
I need help validating the data processing logic in my regulatory reporting visualization.

SYSTEM OVERVIEW:
- Reads Excel file: FR2590_Data_Library_COMPLETE_CORRECTED.xlsx
- Extracts from sheets: MASTER_LINEAGE, MDRM_CATALOG, SCHEDULE_MAP
- Creates nodes: Sources → Atomic CDEs → Transformations → CDEs → MDRMs → Schedules → Report
- Expected: 494 nodes, 634 edges

VALIDATION RESULTS:
✅ All node counts correct
✅ No orphaned nodes
✅ No invalid references
⚠️  123/198 MDRMs have no input connections

QUESTIONS:
1. Is this a data issue (missing info in Excel) or code issue (wrong parsing)?
2. Should all MDRMs have input connections, or is it normal for some to be standalone?
3. How can I improve the connection logic?
4. Are there edge cases I'm missing?

EXCEL STRUCTURE:
- MASTER_LINEAGE has columns: Source_System, Atomic_CDE_ID, Transform_ID, Enriched_CDE_ID, MDRM_Code, Schedule
- MDRM_CATALOG has all 196 MDRMs with metadata
- Some MDRMs in catalog may not appear in MASTER_LINEAGE

CODE:
[Paste integrate_excel_data_corrected.py and relevant sections of sccl_unified_view.py]

Please analyze the data flow logic and suggest improvements.
```

---

## 🔍 Method 3: Google Gemini (Best for Broader Analysis)

### Access: https://gemini.google.com

### Copy-Paste Prompt:

```
Code review request: Financial regulatory data visualization system

TECHNICAL STACK:
- Python 3.x with pandas, pyvis, openpyxl
- JavaScript with vis.js for interactive visualization
- Input: Excel file with multiple sheets
- Output: Interactive HTML network graph

ARCHITECTURE:
1. integrate_excel_data_corrected.py - Reads Excel, creates nodes.csv and edges.csv
2. sccl_unified_view.py - Generates visualization from CSV files
3. Browser renders interactive graph with 494 nodes and 634 edges

PERFORMANCE REQUIREMENTS:
- Load in 2-8 seconds
- Smooth zoom (no lag)
- Handle 500+ nodes efficiently
- Work in modern browsers

VALIDATION FINDINGS:
- Data structure correct (all expected nodes present)
- 123 MDRMs missing input connections
- May be expected if Excel data incomplete

REVIEW REQUEST:
1. Overall code quality assessment
2. Performance optimization opportunities
3. Error handling gaps
4. Security considerations
5. Missing input connections: expected behavior or bug?
6. Suggestions for improvement

FILES:
[Paste both Python files]

Please provide comprehensive analysis with specific recommendations.
```

---

## 📊 Method 4: Compare Results

### Create Comparison Table:

| Model | Strengths | Issues Found | Recommendations |
|-------|-----------|--------------|-----------------|
| **ChatGPT** | | | |
| **Claude** | | | |
| **Gemini** | | | |

### Fill in as you get responses from each model

---

## 🎯 Specific Questions for AI Models

### For Data Accuracy:
```
Given this Excel structure and code, is it normal for 123 out of 198 MDRMs 
to have no input connections? Could this be because:
1. They're calculated MDRMs (formulas only, no direct inputs)?
2. They're in MDRM_CATALOG but not in MASTER_LINEAGE?
3. The code isn't capturing all relationships?

[Paste relevant Excel parsing code]
```

### For Performance:
```
This visualization handles 494 nodes and 634 edges. Current performance:
- Initial load: 3-4 seconds
- Zoom response: 50-80ms
- Filter apply: 30-50ms

Are there optimization opportunities I'm missing?
Physics settings: 100 iterations, Barnes-Hut solver, hierarchical layout

[Paste visualization generation code]
```

### For Code Quality:
```
Review this code for:
- PEP 8 compliance
- Error handling completeness
- Edge case coverage
- Documentation quality
- Test coverage gaps

[Paste code]
```

---

## 🔄 Testing Workflow

### Step 1: Run Validation (Already Done!)
```bash
python3 validate_data.py
```
Result: ⚠️  123 MDRMs have no input connections

### Step 2: Test with ChatGPT
1. Go to https://chat.openai.com
2. Use prompt above
3. Get recommendations
4. Document findings

### Step 3: Test with Claude
1. Go to https://claude.ai
2. Use prompt above
3. Compare with ChatGPT findings
4. Note any differences

### Step 4: Test with Gemini
1. Go to https://gemini.google.com
2. Use prompt above
3. Cross-reference all three models
4. Identify common themes

### Step 5: Implement Changes
Based on consensus from all three models:
1. Fix critical issues
2. Apply recommended optimizations
3. Re-run validation
4. Test visualization

---

## 📋 Quick Testing Checklist

```
Testing Phase 1: Automated
- [ ] Run validate_data.py
- [ ] Check all node counts
- [ ] Verify edge references
- [ ] Document warnings

Testing Phase 2: AI Review
- [ ] Submit to ChatGPT
- [ ] Submit to Claude  
- [ ] Submit to Gemini
- [ ] Compare results
- [ ] Document consensus issues

Testing Phase 3: Manual
- [ ] Visual inspection
- [ ] Browser testing
- [ ] Performance check
- [ ] User experience test

Testing Phase 4: Domain Validation
- [ ] Share with regulatory experts
- [ ] Verify data accuracy
- [ ] Confirm business logic
- [ ] Get sign-off
```

---

## 🎓 Pro Tips

### When Using AI Models:

1. **Be Specific**
   - Provide context about your domain
   - Share expected behavior
   - Include validation results

2. **Share Code in Chunks**
   - If file too large, split into logical sections
   - Focus on areas with known issues
   - Include relevant comments

3. **Ask Follow-up Questions**
   ```
   "You mentioned X could be improved. Can you show me the specific code change?"
   "Why is approach Y better than what I have?"
   "What are the trade-offs of your suggestion?"
   ```

4. **Request Alternatives**
   ```
   "What are 3 different ways to solve this problem?"
   "Which approach would you recommend and why?"
   ```

5. **Validate Suggestions**
   - Don't blindly apply all suggestions
   - Test each change independently
   - Re-run validation after changes

---

## 📊 Expected Outcomes

After testing with all three models, you should have:

### ✅ **Confirmed**
- Whether 123 unconnected MDRMs is expected or a bug
- Specific code improvements to make
- Performance optimization opportunities
- Missing error handling

### ✅ **Action Items**
1. Fix critical issues (if any)
2. Apply recommended improvements
3. Add missing error handling
4. Optimize performance
5. Improve documentation

### ✅ **Validation**
- Re-run `validate_data.py` to confirm fixes
- Test visualization thoroughly
- Get domain expert sign-off

---

## 🚀 Next Steps

1. **Right now:**
   ```bash
   # Already ran this and got results!
   python3 validate_data.py
   ```

2. **Next (10 minutes):**
   - Open ChatGPT
   - Copy validation results + code
   - Get first AI review

3. **Then (10 minutes):**
   - Open Claude
   - Same process
   - Compare with ChatGPT results

4. **Finally (10 minutes):**
   - Open Gemini
   - Same process
   - Create consolidated findings document

5. **Implement (30-60 minutes):**
   - Make recommended changes
   - Test thoroughly
   - Re-validate

---

## 📝 Sample Response Template

Use this to document AI model responses:

```markdown
# AI Model Testing Results

## Date: [Today's Date]

### ChatGPT Review
**Main Findings:**
1. [Finding 1]
2. [Finding 2]

**Recommendations:**
1. [Rec 1]
2. [Rec 2]

**Severity:** HIGH / MEDIUM / LOW

---

### Claude Review
**Main Findings:**
1. [Finding 1]
2. [Finding 2]

**Recommendations:**
1. [Rec 1]
2. [Rec 2]

**Severity:** HIGH / MEDIUM / LOW

---

### Gemini Review
**Main Findings:**
1. [Finding 1]
2. [Finding 2]

**Recommendations:**
1. [Rec 1]
2. [Rec 2]

**Severity:** HIGH / MEDIUM / LOW

---

### Consensus Issues (All 3 Models Agree):
1. [Issue that all models identified]

### Conflicting Opinions:
1. [Area where models disagree]

### Action Plan:
1. [ ] [Action item 1]
2. [ ] [Action item 2]
```

---

**You're Ready!** Your validation script is already run and working. Now just copy the prompts above and test with the AI models! 🚀
