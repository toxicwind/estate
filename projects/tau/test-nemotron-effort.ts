import { getEffort } from './engine/packages/ai/src/routing/nemotron-effort';
const log: string[] = [];
function l(s: string) { log.push(s); }
// Test cases for super models
l('=== Testing Super Models ===');
l(`super + none: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'none')}`);
l(`super + low: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'low')}`);
l(`super + medium: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'medium')}`);
l(`super + high: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'high')}`);
l(`super + xhigh: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'xhigh')}`);
l(`super + max: ${getEffort('nvidia/nemotron-3-super-120b-a12b', 'max')}`);
// Test cases for lightning models
l('\n=== Testing Lightning Models ===');
l(`lightning + none: ${getEffort('nvidia/nemotron-3.5-lightning-30b-a3b', 'none')}`);
l(`lightning + medium: ${getEffort('nvidia/nemotron-3.5-lightning-30b-a3b', 'medium')}`);
l(`lightning + high: ${getEffort('nvidia/nemotron-3.5-lightning-30b-a3b', 'high')}`);
l(`lightning + xhigh: ${getEffort('nvidia/nemotron-3.5-lightning-30b-a3b', 'xhigh')}`);
l(`lightning + max: ${getEffort('nvidia/nemotron-3.5-lightning-30b-a3b', 'max')}`);
// Test invalid model (should default to lightning map)
l('\n=== Testing Invalid Model (defaults to lightning) ===');
l(`invalid + none: ${getEffort('unknown/model', 'none')}`);
l(`invalid + xhigh: ${getEffort('unknown/model', 'xhigh')}`);
// Write log
const fs = await import('node:fs');
fs.writeFileSync('nemotron-effort-test.log', log.join('\n'));
